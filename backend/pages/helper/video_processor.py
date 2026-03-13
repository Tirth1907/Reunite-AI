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
from pages.helper.fallback_detector import (
    detect_face_fallback,
    has_face_loose,
    get_fallback_frame_interval,
    upscale_if_small,
    apply_clahe,
    FALLBACK_DISTANCE_THRESHOLD,
    FALLBACK_MIN_CONFIDENCE,
    FALLBACK_MIN_FACE_SIZE,
    FALLBACK_MIN_EMBEDDING_NORM,
)
from pages.helper.yolo_prescreener import (
    has_face_yolo,
    is_yolo_available,
)

# ============================================================
# SPEED-CRITICAL FILE — READ BEFORE MODIFYING
# ============================================================
# PROTECTED FILES (DO NOT MODIFY):
#   backend/pages/helper/registration_encoder.py
#   backend/pages/helper/fallback_detector.py
#
# FALLBACK PASS RULES:
#   All fallback detection logic lives in fallback_detector.py
#   Do NOT add DeepFace calls directly in the fallback pass here
#   Do NOT add retry loops in the fallback pass
#   Do NOT use retinaface in the fallback pass
#   Do NOT disable has_face_loose() pre-filter
#
# PASS 1 RULES:
#   Pass 1 uses retinaface — do NOT change this
#   Pass 1 thresholds: distance=0.40, confidence=60%
#   Do NOT modify Pass 1 when fixing fallback issues
#
# After any change to this file, run:
#   python backend/test_speed.py
#   python backend/test_registration.py
# ============================================================

# ============================================================
# IMPORTANT: THIS FILE HANDLES VIDEO PROCESSING ONLY
# ============================================================
# Do NOT add registration logic to this file.
# Do NOT copy preprocessing patterns from here to cases.py
# Do NOT modify Pass 1 logic when improving fallback pass.
#
# Registration embedding extraction lives in:
# backend/pages/helper/registration_encoder.py
#
# Pass 1 (strict CCTV) and fallback pass are separate code paths.
# Modifying the fallback pass must never affect Pass 1.
# ============================================================

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRAME_INTERVAL_SECONDS = 3        # Legacy default (overridden by adaptive sampling below)
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
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
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


def _detect_and_embed(frame_rgb, is_fallback_pass=False, yolo_boxes=None):
    """
    Extract face embeddings from a frame.
    Pass 1 uses YOLO boxes to crop the face, then ArcFace embedding ONLY on the cropped face.
    Bypasses RetinaFace entirely (uses detector_backend="skip").
    """
    from deepface import DeepFace
    faces = []

    if yolo_boxes is not None and len(yolo_boxes) > 0:
        h_frame, w_frame = frame_rgb.shape[:2]
        for box in yolo_boxes:
            x1, y1, x2, y2 = box.get("x1", 0), box.get("y1", 0), box.get("x2", 0), box.get("y2", 0)
            
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w_frame, x2), min(h_frame, y2)
            
            if x2 <= x1 or y2 <= y1:
                continue
                
            face_crop = frame_rgb[y1:y2, x1:x2]
            if face_crop.size == 0:
                continue
                
            try:
                results = DeepFace.represent(
                    img_path=face_crop,
                    model_name="ArcFace",
                    detector_backend="skip",
                    enforce_detection=False,
                    align=True,
                )
                if results:
                    embedding = results[0].get("embedding")
                    if embedding:
                        facial_area = {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1}
                        faces.append((embedding, facial_area))
            except Exception:
                continue
        return faces

    # Fallback to OpenCV if no yolo_boxes provided
    try:
        results = DeepFace.represent(
            img_path=frame_rgb,
            model_name="ArcFace",
            detector_backend="opencv",
            enforce_detection=False,
            align=True,
        )
        if not results:
            return []
        for res in results:
            embedding = res.get("embedding")
            facial_area = res.get("facial_area", {})
            face_confidence = res.get("face_confidence", 1.0)
            if embedding and face_confidence >= 0.50:
                face_w = facial_area.get("w", 0)
                face_h = facial_area.get("h", 0)
                if face_w >= 30 and face_h >= 30:
                    faces.append((embedding, facial_area))
        return faces
    except Exception:
        return []


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
# Processing Pass Helper
# ---------------------------------------------------------------------------

def get_adaptive_frame_interval(duration_seconds: float, is_fallback_pass: bool = False) -> int:
    """
    Returns frame extraction interval in seconds.
    Pass 1 uses adaptive intervals based on video length to reduce total frames.
    Fallback pass uses denser sampling for short videos
    to maximize detection chances.
    """
    if is_fallback_pass:
        # Denser sampling in fallback for better detection
        if duration_seconds <= 90:      return 1   # short: every 1s
        elif duration_seconds <= 300:   return 2   # 1.5-5 min: every 2s
        elif duration_seconds <= 600:   return 4   # 5-10 min: every 4s
        elif duration_seconds <= 900:   return 6   # 10-15 min: every 6s
        else:                           return 10  # over 15 min: every 10s
    else:
        # Pass 1: Aggressive adaptive sampling to reduce processing time
        # video < 60s → every 0.5s, 1-5min → every 1s, 5-20min → every 2s, >20min → every 3s
        if duration_seconds <= 120:     return 3
        elif duration_seconds <= 300:   return 5
        elif duration_seconds <= 600:   return 8
        elif duration_seconds <= 900:   return 12
        else:                           return 15


def _run_processing_pass(
    video_path: str,
    case_embedding,
    video_id: str,
    case_id: str,
    confidence_threshold: float,
    min_confidence_percent: int,
    is_fallback_pass: bool = False,
):
    """
    Run a single processing pass over the video.

    Extracts frames, detects faces, generates embeddings, compares against
    the target embedding, and saves matched detections.

    When is_fallback_pass=True, every saved detection is tagged with
    is_low_confidence=True.

    Returns the number of detections saved during this pass.
    """
    pass_label = "PASS-2-FALLBACK" if is_fallback_pass else "PASS-1-STRICT"
    logger.info(
        f"[VIDEO] [{pass_label}] Starting pass: threshold={confidence_threshold}, "
        f"min_conf={min_confidence_percent}%, fallback={is_fallback_pass}"
    )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video file: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration_seconds = total_video_frames / fps if fps > 0 else 0

        # Calculate how many frames we'll extract (adaptive)
        if is_fallback_pass:
            interval_seconds = get_fallback_frame_interval(video_duration_seconds)
        else:
            interval_seconds = get_adaptive_frame_interval(video_duration_seconds)

        extraction_times = []
        t = 0.0
        while t < video_duration_seconds:
            extraction_times.append(t)
            t += float(interval_seconds)

        total_frames_to_process = len(extraction_times)

        logger.info(
            f"[VIDEO] [{pass_label}] Video info: fps={fps:.1f}, total_frames={total_video_frames}, "
            f"duration={video_duration_seconds:.1f}s, frames_to_extract={total_frames_to_process}"
        )

        # Update total frames in DB (only on first pass)
        if not is_fallback_pass:
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
            target_frame_number = int(timestamp_sec * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_number)
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
            if is_fallback_pass:
                if not has_face_loose(frame_bgr):
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
            else:
                # Use YOLO pre-screener first (faster, ~15ms), fall back to Haar
                face_detected = False
                yolo_boxes = None
                face_detected = _has_faces_fast(frame_bgr)

                if not face_detected:
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
            if is_fallback_pass:
                frame_rgb = apply_clahe(frame_rgb)
                results = detect_face_fallback(frame_rgb)
                faces = []
                for res in results:
                    embedding = res.get("embedding")
                    facial_area = res.get("facial_area", {})
                    if not embedding: continue
                    face_w = facial_area.get("w", 0)
                    face_h = facial_area.get("h", 0)
                    if face_w < FALLBACK_MIN_FACE_SIZE or face_h < FALLBACK_MIN_FACE_SIZE:
                        continue
                    if np.linalg.norm(embedding) <= FALLBACK_MIN_EMBEDDING_NORM:
                        continue
                    faces.append((embedding, facial_area))
            else:
                faces = _detect_and_embed(frame_rgb, is_fallback_pass=False)

            # ---- Rule 1: Only process the BEST face match per frame ----
            best_frame_match = None  # (distance, confidence, embedding_arr, facial_area)

            for embedding, facial_area in faces:
                embedding_arr = np.array(embedding, dtype=np.float64)

                if len(embedding_arr) != len(case_embedding):
                    continue

                distance = _cosine_distance(case_embedding, embedding_arr)
                confidence = (1.0 - distance) * 100.0

                if is_fallback_pass:
                    if (distance <= FALLBACK_DISTANCE_THRESHOLD and
                            confidence >= FALLBACK_MIN_CONFIDENCE):
                        if best_frame_match is None or confidence > best_frame_match[1]:
                            best_frame_match = (distance, confidence, embedding_arr, facial_area)
                    else:
                        logger.info(
                            f"[FILTER] [{pass_label}] Rejected at {timestamp_sec:.1f}s, "
                            f"conf={confidence:.1f}%, dist={distance:.4f}"
                        )
                else:
                    if distance <= confidence_threshold and confidence >= min_confidence_percent:
                        if best_frame_match is None or confidence > best_frame_match[1]:
                            best_frame_match = (distance, confidence, embedding_arr, facial_area)
                    else:
                        logger.info(
                            f"[FILTER] [{pass_label}] Rejected at {timestamp_sec:.1f}s, "
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
                            f"[DEDUP] [{pass_label}] Suppressed at {timestamp_sec:.1f}s: "
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
                        is_low_confidence=is_fallback_pass,
                    )

                    detections_buffer.append(detection)
                    detection_count += 1
                    last_saved_timestamp = timestamp_sec
                    last_saved_embedding = embedding_arr

                    logger.info(
                        f"[VIDEO] [{pass_label}] SAVED at {timestamp_sec:.1f}s: "
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
                logger.info(
                    f"[VIDEO] [{pass_label}] Progress: {processed}/{total_frames_to_process} frames, "
                    f"{detection_count} detections, {skipped_no_face} skipped"
                )

        # ---- Flush remaining detections ----
        if detections_buffer:
            db_queries.save_video_detections_batch(detections_buffer)
            detections_buffer = []

        logger.info(
            f"[VIDEO] [{pass_label}] COMPLETE: frames={processed}, "
            f"detections={detection_count}, skipped_no_face={skipped_no_face}"
        )

        return detection_count

    finally:
        cap.release()


# ---------------------------------------------------------------------------
# Main Processing Pipeline (Two-Pass)
# ---------------------------------------------------------------------------

def process_video(video_id: str):
    """
    Main entry point for background video processing.

    Two-pass system:
      Pass 1 — Strict thresholds (existing logic, unchanged)
      Pass 2 — Fallback with relaxed thresholds (only if Pass 1 finds 0 detections)

    1. Loads the target case embedding from the database
    2. Runs Pass 1 with strict thresholds
    3. If Pass 1 finds 0 detections, runs Pass 2 with fallback thresholds
    4. Saves detections to the database
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

    # Clamp: never allow distance threshold above DEFAULT_CONFIDENCE_THRESHOLD
    if threshold > DEFAULT_CONFIDENCE_THRESHOLD:
        logger.warning(
            f"[VIDEO] Clamping user threshold {threshold} -> {DEFAULT_CONFIDENCE_THRESHOLD}"
        )
        threshold = DEFAULT_CONFIDENCE_THRESHOLD

    # ---- Update status to processing ----
    db_queries.update_video_status(video_id, status="processing")

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

        # ==================================================================
        # PASS 1 — Strict thresholds (existing logic, completely unchanged)
        # ==================================================================
        pass1_count = _run_processing_pass(
            video_path=file_path,
            case_embedding=target_embedding,
            video_id=video_id,
            case_id=case_id,
            confidence_threshold=threshold,
            min_confidence_percent=MIN_CONFIDENCE_PERCENT,
            is_fallback_pass=False,
        )

        # Check how many detections Pass 1 actually saved
        db_detection_count = db_queries.get_detection_count_for_video(video_id)

        if db_detection_count == 0:
            # ==============================================================
            # PASS 2 — Fallback with relaxed thresholds
            # ==============================================================
            logger.info(
                f"[VIDEO] Pass 1 found 0 detections. Triggering fallback Pass 2 "
                f"(threshold={FALLBACK_DISTANCE_THRESHOLD}, "
                f"min_conf={FALLBACK_MIN_CONFIDENCE}%)"
            )

            pass2_count = _run_processing_pass(
                video_path=file_path,
                case_embedding=target_embedding,
                video_id=video_id,
                case_id=case_id,
                confidence_threshold=FALLBACK_DISTANCE_THRESHOLD,
                min_confidence_percent=FALLBACK_MIN_CONFIDENCE,
                is_fallback_pass=True,
            )

            # Mark that fallback was used on the upload record
            db_queries.update_video_fallback(video_id, used_fallback=True)

            total_detections = pass2_count
            logger.info(f"[VIDEO] Pass 2 completed with {pass2_count} detections.")
        else:
            total_detections = db_detection_count
            logger.info(
                f"[VIDEO] Pass 1 found {db_detection_count} detections. "
                f"Fallback not needed."
            )

        # ---- Mark as complete ----
        db_queries.update_video_status(
            video_id,
            status="done",
            total_detections=total_detections,
            completed_at=datetime.utcnow(),
        )

        logger.info(
            f"[VIDEO] ========== COMPLETE: video={video_id}, "
            f"total_detections={total_detections} =========="
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
        logger.info(f"[VIDEO] Resources released for video {video_id}")
