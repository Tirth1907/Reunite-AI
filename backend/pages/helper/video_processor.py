"""
Reunite AI Phase 2 — Offline CCTV Batch Video Processor

Processes uploaded CCTV videos frame-by-frame:
1. Extracts frames every 2 seconds at 640x480
2. Detects faces using RetinaFace
3. Generates ArcFace embeddings
4. Compares against a single missing case embedding
5. Saves matched detections with cropped face images

Designed for:
- GTX 1650 (4GB VRAM) with CPU fallback
- 16GB RAM, sequential processing
- Up to 15-minute videos
"""

import os
import json
import uuid
import logging
import traceback
from datetime import datetime

import cv2
import numpy as np
import PIL.Image

from pages.helper import db_queries
from pages.helper.data_models import VideoDetections

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRAME_INTERVAL_SECONDS = 3        # Extract one frame every 3 seconds (balances speed vs coverage)
TARGET_MAX_WIDTH = 1280            # Max width (only downscale, never upscale)
TARGET_MAX_HEIGHT = 720            # Max height
DEFAULT_CONFIDENCE_THRESHOLD = 0.40  # Cosine distance threshold (distance <= 0.40 = confidence >= 60%)
PROGRESS_UPDATE_INTERVAL = 10     # Update DB progress every N frames
SUPPRESSION_WINDOW_SEC = 3        # Suppress similar consecutive detections within this gap
SUPPRESSION_SIMILARITY = 0.10     # Cosine distance below this = same face (skip)
MIN_CONFIDENCE_PERCENT = 60       # Hard floor: never save detections below this confidence
MAX_VIDEO_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIDEO_UPLOADS_DIR = os.path.join(BASE_DIR, "video_uploads")
DETECTIONS_DIR = os.path.join(BASE_DIR, "resources", "video_detections")

# Ensure directories exist
os.makedirs(VIDEO_UPLOADS_DIR, exist_ok=True)
os.makedirs(DETECTIONS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# GPU / CPU Detection
# ---------------------------------------------------------------------------
_device_info = None


def get_device_info():
    """Detect CUDA availability and configure TensorFlow VRAM limits."""
    global _device_info
    if _device_info is not None:
        return _device_info

    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            # Limit VRAM to 2GB to leave headroom on 4GB GTX 1650
            try:
                tf.config.set_logical_device_configuration(
                    gpus[0],
                    [tf.config.LogicalDeviceConfiguration(memory_limit=2048)],
                )
            except RuntimeError:
                # Virtual devices must be set before GPUs are initialized
                pass
            _device_info = {
                "device": "GPU",
                "name": gpus[0].name,
                "vram_limit_mb": 2048,
            }
            logger.info(f"[VIDEO] GPU detected: {gpus[0].name}, VRAM limited to 2048 MB")
            return _device_info
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"[VIDEO] GPU detection failed: {e}")

    # CPU fallback
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    _device_info = {"device": "CPU", "name": "CPU fallback", "vram_limit_mb": 0}
    logger.info("[VIDEO] Using CPU fallback (no CUDA GPU detected)")
    return _device_info


# ---------------------------------------------------------------------------
# DeepFace lazy loader
# ---------------------------------------------------------------------------
_deepface_loaded = False


def _ensure_deepface():
    """Lazy-import DeepFace so the server starts fast."""
    global _deepface_loaded
    if _deepface_loaded:
        return True
    try:
        get_device_info()  # configure GPU first
        from deepface import DeepFace  # noqa: F401
        _deepface_loaded = True
        logger.info("[VIDEO] DeepFace loaded successfully")
        return True
    except ImportError:
        logger.error("[VIDEO] DeepFace is not installed")
        return False


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Haar cascade pre-filter (lightweight face check ~3-5ms per frame)
# ---------------------------------------------------------------------------
_haar_cascade = None


def _get_haar_cascade():
    """Lazy-load the OpenCV Haar cascade for fast face pre-filtering."""
    global _haar_cascade
    if _haar_cascade is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _haar_cascade = cv2.CascadeClassifier(cascade_path)
    return _haar_cascade


def _has_faces_fast(frame_bgr):
    """
    Lightweight pre-filter using OpenCV Haar cascade.
    Returns True if at least one face-like region is detected.
    Runs in ~3-5ms, used to skip expensive DeepFace on empty frames.
    """
    cascade = _get_haar_cascade()
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=3,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    return len(faces) > 0


def _cosine_distance(a, b):
    """Cosine distance between two vectors. Returns 0.0 (identical) to 2.0."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1.0 - (np.dot(a, b) / (norm_a * norm_b))


def _detect_and_embed(frame_rgb):
    """
    Detect faces in a frame and return list of (embedding, facial_area).

    Uses a multi-strategy approach for robustness with CCTV footage:
    1. Try enforce_detection=True first (only real detected faces)
    2. Fall back to enforce_detection=False if no faces found
    3. Try both RetinaFace and OpenCV backends
    4. Skip alignment if aligned version fails (handles missing landmarks)

    Each facial_area is a dict with keys: x, y, w, h.
    """
    from deepface import DeepFace

    faces = []

    # Strategy list: (detector_backend, enforce, align, label)
    # Only 2 strategies — Haar pre-filter already confirmed a face exists
    strategies = [
        ("retinaface", True, True, "retina+enforce+align"),
        ("opencv", True, True, "opencv+enforce+align"),
    ]

    for detector, enforce, align, label in strategies:
        try:
            results = DeepFace.represent(
                img_path=frame_rgb,
                model_name="ArcFace",
                detector_backend=detector,
                enforce_detection=enforce,
                align=align,
            )
        except Exception:
            # enforce_detection=True raises when no face found — that's expected
            continue

        if not results:
            continue

        for obj in results:
            embedding = obj.get("embedding")
            facial_area = obj.get("facial_area", {})

            if not embedding or len(embedding) == 0:
                continue

            emb_arr = np.array(embedding, dtype=np.float64)

            # Quality check: skip garbage embeddings (near-zero norm)
            norm = np.linalg.norm(emb_arr)
            if norm < 1.0:
                continue

            # Quality check: skip if facial area is too small (likely noise)
            face_w = facial_area.get("w", 0)
            face_h = facial_area.get("h", 0)
            if face_w > 0 and face_h > 0 and (face_w < 15 or face_h < 15):
                continue

            faces.append((embedding, facial_area))

        # If this strategy found valid faces, use them
        if faces:
            logger.debug(f"[VIDEO] Strategy '{label}' found {len(faces)} face(s)")
            break

    return faces


def _crop_face(frame_rgb, facial_area, padding=20):
    """Crop a face region from the frame with padding."""
    h, w = frame_rgb.shape[:2]
    x = max(0, facial_area.get("x", 0) - padding)
    y = max(0, facial_area.get("y", 0) - padding)
    x2 = min(w, facial_area.get("x", 0) + facial_area.get("w", 0) + padding)
    y2 = min(h, facial_area.get("y", 0) + facial_area.get("h", 0) + padding)

    if x2 <= x or y2 <= y:
        return None

    cropped = frame_rgb[y:y2, x:x2]
    return cropped


def _save_cropped_face(cropped_rgb, detection_id):
    """Save a cropped face image as JPEG. Returns the relative path."""
    filename = f"{detection_id}.jpg"
    filepath = os.path.join(DETECTIONS_DIR, filename)
    # Convert RGB to BGR for OpenCV saving
    cropped_bgr = cv2.cvtColor(cropped_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(filepath, cropped_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return f"video_detections/{filename}"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv"}


def validate_video_file(file_path):
    """Validate that the file is a playable video. Returns (ok, error_msg)."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported format: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    file_size = os.path.getsize(file_path)
    if file_size > MAX_VIDEO_SIZE_BYTES:
        return False, f"File too large: {file_size / (1024**3):.1f} GB. Max: 2 GB"

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        cap.release()
        return False, "Cannot open video file. It may be corrupt."

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if fps <= 0 or frame_count <= 0:
        return False, "Invalid video: cannot determine FPS or frame count."

    duration_sec = frame_count / fps
    if duration_sec > 1800:  # 30 minutes max
        return False, f"Video too long: {duration_sec/60:.0f} minutes. Max: 30 minutes."

    return True, None


# ---------------------------------------------------------------------------
# Main Processing Pipeline
# ---------------------------------------------------------------------------

def process_video(video_id: str):
    """
    Main entry point for background video processing.

    1. Loads the target case embedding from the database
    2. Opens the video with OpenCV
    3. Extracts frames every 2 seconds
    4. Detects faces and generates embeddings
    5. Matches against the target case
    6. Saves detections to the database
    """
    logger.info(f"[VIDEO] ========== Starting processing for video {video_id} ==========")

    # ---- Load upload record ----
    upload = db_queries.get_video_upload(video_id)
    if not upload:
        logger.error(f"[VIDEO] Upload record {video_id} not found in database")
        return

    case_id = upload.case_id
    file_path = upload.file_path
    threshold = upload.confidence_threshold

    # Clamp: never allow distance threshold above MATCH_DISTANCE_THRESHOLD
    if threshold > DEFAULT_CONFIDENCE_THRESHOLD:
        logger.warning(
            f"[VIDEO] Clamping user threshold {threshold} -> {DEFAULT_CONFIDENCE_THRESHOLD}"
        )
        threshold = DEFAULT_CONFIDENCE_THRESHOLD

    # ---- Update status to processing ----
    db_queries.update_video_status(video_id, status="processing")

    cap = None
    try:
        # ---- Load target case embedding ----
        face_mesh_json = db_queries.get_case_embedding(case_id)
        if not face_mesh_json:
            raise ValueError(f"Case {case_id} has no face embedding in the database")

        target_embedding = json.loads(face_mesh_json)
        if not target_embedding or len(target_embedding) == 0:
            raise ValueError(f"Case {case_id} has an empty/invalid face embedding")

        target_embedding = np.array(target_embedding, dtype=np.float64)
        logger.info(f"[VIDEO] Target embedding loaded: case={case_id}, dim={len(target_embedding)}")

        # ---- Ensure DeepFace is ready ----
        if not _ensure_deepface():
            raise RuntimeError("DeepFace is not available. Install with: pip install deepface")

        # ---- Open video ----
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video file: {file_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_video_frames / fps if fps > 0 else 0

        # Calculate how many frames we'll extract (one every FRAME_INTERVAL_SECONDS)
        extraction_times = []
        t = 0.0
        while t < duration_sec:
            extraction_times.append(t)
            t += FRAME_INTERVAL_SECONDS

        total_frames_to_process = len(extraction_times)

        logger.info(
            f"[VIDEO] Video info: fps={fps:.1f}, total_frames={total_video_frames}, "
            f"duration={duration_sec:.1f}s, frames_to_extract={total_frames_to_process}"
        )

        # Update total frames in DB
        db_queries.update_video_status(
            video_id, status="processing", total_frames=total_frames_to_process
        )

        # ---- Frame-by-frame processing ----
        detections_buffer = []
        processed = 0
        detection_count = 0
        skipped_no_face = 0

        # Dedup state — simple: track last saved timestamp + embedding
        last_saved_timestamp = -999.0
        last_saved_embedding = None  # np.ndarray or None

        # Rule 3: Ensure DB unique index exists
        db_queries.ensure_video_detections_index()

        for frame_idx, timestamp_sec in enumerate(extraction_times):
            # Seek to the frame at the given timestamp
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
            ret, frame_bgr = cap.read()

            if not ret or frame_bgr is None:
                processed += 1
                continue

            # Resize only if frame is larger than max (preserve quality for CCTV)
            h_orig, w_orig = frame_bgr.shape[:2]
            if w_orig > TARGET_MAX_WIDTH or h_orig > TARGET_MAX_HEIGHT:
                scale = min(TARGET_MAX_WIDTH / w_orig, TARGET_MAX_HEIGHT / h_orig)
                new_w = int(w_orig * scale)
                new_h = int(h_orig * scale)
                frame_bgr = cv2.resize(frame_bgr, (new_w, new_h))

            # --- Fast pre-filter: skip frames with no faces ---
            if not _has_faces_fast(frame_bgr):
                skipped_no_face += 1
                processed += 1
                del frame_bgr
                if processed % PROGRESS_UPDATE_INTERVAL == 0:
                    db_queries.update_video_status(
                        video_id,
                        status="processing",
                        processed_frames=processed,
                        total_detections=detection_count,
                    )
                continue

            # Convert BGR -> RGB for DeepFace
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            # Detect faces and get embeddings
            faces = _detect_and_embed(frame_rgb)

            # ---- Rule 1: Only process the BEST face match per frame ----
            best_frame_match = None  # (distance, confidence, embedding_arr, facial_area)

            for embedding, facial_area in faces:
                embedding_arr = np.array(embedding, dtype=np.float64)

                if len(embedding_arr) != len(target_embedding):
                    continue

                distance = _cosine_distance(target_embedding, embedding_arr)
                confidence = (1.0 - distance) * 100.0

                if distance <= threshold and confidence >= MIN_CONFIDENCE_PERCENT:
                    if best_frame_match is None or confidence > best_frame_match[1]:
                        best_frame_match = (distance, confidence, embedding_arr, facial_area)
                else:
                    logger.info(
                        f"[FILTER] Rejected at {timestamp_sec:.1f}s, "
                        f"conf={confidence:.1f}%, dist={distance:.4f}"
                    )

            # ---- Rule 2: Suppress consecutive similar detections ----
            if best_frame_match is not None:
                _, confidence, embedding_arr, facial_area = best_frame_match

                suppressed = False
                time_gap = timestamp_sec - last_saved_timestamp

                if time_gap < SUPPRESSION_WINDOW_SEC and last_saved_embedding is not None:
                    face_dist = _cosine_distance(last_saved_embedding, embedding_arr)
                    if face_dist < SUPPRESSION_SIMILARITY:
                        logger.info(
                            f"[DEDUP] Suppressed at {timestamp_sec:.1f}s: "
                            f"gap={time_gap:.1f}s, face_dist={face_dist:.4f}"
                        )
                        suppressed = True

                if not suppressed:
                    # Save this detection
                    detection_id = str(uuid.uuid4())
                    cropped = _crop_face(frame_rgb, facial_area)
                    if cropped is not None and cropped.size > 0:
                        cropped_path = _save_cropped_face(cropped, detection_id)
                    else:
                        cropped_path = _save_cropped_face(frame_rgb, detection_id)

                    detection = VideoDetections(
                        id=detection_id,
                        video_id=video_id,
                        case_id=case_id,
                        timestamp_seconds=round(timestamp_sec, 2),
                        confidence=round(confidence, 2),
                        cropped_face_path=cropped_path,
                        frame_number=frame_idx,
                    )

                    detections_buffer.append(detection)
                    detection_count += 1
                    last_saved_timestamp = timestamp_sec
                    last_saved_embedding = embedding_arr

                    logger.info(
                        f"[VIDEO] SAVED at {timestamp_sec:.1f}s: "
                        f"conf={confidence:.1f}%, id={detection_id[:8]}"
                    )

            # Release frame memory
            del frame_bgr, frame_rgb

            processed += 1

            # Flush detections and update progress periodically
            if processed % PROGRESS_UPDATE_INTERVAL == 0:
                if detections_buffer:
                    db_queries.save_video_detections_batch(detections_buffer)
                    detections_buffer = []
                db_queries.update_video_status(
                    video_id,
                    status="processing",
                    processed_frames=processed,
                    total_detections=detection_count,
                )
                logger.info(f"[VIDEO] Progress: {processed}/{total_frames_to_process} frames, {detection_count} detections, {skipped_no_face} skipped")

        # ---- Flush remaining detections ----
        if detections_buffer:
            db_queries.save_video_detections_batch(detections_buffer)
            detections_buffer = []

        # ---- Mark as complete ----
        db_queries.update_video_status(
            video_id,
            status="done",
            processed_frames=processed,
            total_detections=detection_count,
            completed_at=datetime.utcnow(),
        )

        logger.info(
            f"[VIDEO] ========== COMPLETE: video={video_id}, "
            f"frames={processed}, detections={detection_count}, "
            f"skipped_no_face={skipped_no_face} =========="
        )

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"[VIDEO] Processing FAILED for video {video_id}: {error_msg}")
        traceback.print_exc()
        db_queries.update_video_status(
            video_id,
            status="failed",
            error_message=error_msg[:500],
        )

    finally:
        if cap is not None:
            cap.release()
        logger.info(f"[VIDEO] Resources released for video {video_id}")
