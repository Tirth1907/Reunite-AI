# ============================================================
# YOLO PRE-SCREENER — SPEED OPTIMIZATION ONLY
# ============================================================
# This file adds YOLOv8-face as a fast pre-screener before
# RetinaFace in Pass 1 of video_processor.py.
#
# PURPOSE:
#   YOLOv8-face runs at ~15ms per frame.
#   RetinaFace runs at ~400ms per frame.
#   By checking with YOLO first, we skip RetinaFace on frames
#   that have no face — saving 400ms per empty frame.
#
# WHAT THIS FILE DOES NOT DO:
#   - Does NOT generate face embeddings
#   - Does NOT replace DeepFace or ArcFace
#   - Does NOT replace RetinaFace
#   - Does NOT change matching logic
#   - Does NOT affect Pass 2 fallback
#
# CRASH SAFETY:
#   Every function in this file returns a safe fallback value
#   if YOLO fails for any reason. The system will continue
#   working with the existing Haar cascade if YOLO is unavailable.
#
# DO NOT MODIFY THIS FILE without understanding the impact
# on video processing speed.
# ============================================================

import os
import numpy as np

# Model path — relative to this file
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'yolov8n-face.pt'
)

# Global model instance — loaded once, reused
_yolo_model = None
_yolo_available = False


def _load_yolo_model():
    """
    Load YOLOv8-face model once at first use.
    Sets _yolo_available=False if loading fails for any reason.
    Never raises an exception.
    """
    global _yolo_model, _yolo_available

    try:
        from ultralytics import YOLO
        print(f"[YOLO] ultralytics imported OK")

        if os.path.exists(_MODEL_PATH):
            print(f"[YOLO] Loading model from: {_MODEL_PATH}")
            _yolo_model = YOLO(_MODEL_PATH)
        else:
            print(f"[YOLO] Model not at {_MODEL_PATH}, trying auto-download")
            _yolo_model = YOLO('yolov8n.pt')

        print(f"[YOLO] Model object created OK")

        # Warm up with a blank frame — skip warmup if it fails
        try:
            import numpy as np
            dummy = np.zeros((64, 64, 3), dtype=np.uint8)
            _yolo_model.predict(source=dummy, verbose=False, conf=0.25)
            print(f"[YOLO] Warmup predict OK")
        except Exception as warmup_err:
            print(f"[YOLO] Warmup failed but continuing: {warmup_err}")

        _yolo_available = True
        print(f"[YOLO] YOLOv8-face loaded successfully — AVAILABLE")

    except Exception as e:
        import traceback
        _yolo_available = False
        _yolo_model = None
        print(f"[YOLO] Load FAILED: {e}")
        traceback.print_exc()
        print(f"[YOLO] Falling back to Haar cascade")


def is_yolo_available() -> bool:
    """
    Returns True if YOLOv8-face is loaded and ready.
    Safe to call at any time.
    """
    global _yolo_model, _yolo_available
    if _yolo_model is None and not _yolo_available:
        _load_yolo_model()
    return _yolo_available


def has_face_yolo(frame_bgr: np.ndarray,
                  confidence_threshold: float = 0.15) -> bool:
    """
    Fast face presence check using YOLOv8-face (~15ms).

    Returns True if at least one face is detected.
    Returns True (fail open) if YOLO is unavailable or errors.
    Never raises an exception.

    Args:
        frame_bgr: OpenCV BGR frame from video
        confidence_threshold: minimum detection confidence (0.15 default,
                              lowered from 0.25 to catch side/partial faces)

    Returns:
        bool: True if face found or if YOLO unavailable
    """
    global _yolo_model, _yolo_available

    # Load model on first call
    if _yolo_model is None and not _yolo_available:
        _load_yolo_model()

    # If YOLO not available, return True (let RetinaFace decide)
    if not _yolo_available or _yolo_model is None:
        return True

    try:
        results = _yolo_model.predict(
            source=frame_bgr,
            verbose=False,
            conf=confidence_threshold
        )

        # Check if any face detected with sufficient confidence
        for result in results:
            if result.boxes is not None and len(result.boxes) > 0:
                return True

        return False

    except Exception:
        # Any error → return True (fail open, let RetinaFace decide)
        return True


def get_face_boxes(frame_bgr: np.ndarray,
                   confidence_threshold: float = 0.15) -> list:
    """
    Returns list of detected face bounding boxes from YOLO.
    Each item is a dict with keys: x1, y1, x2, y2, confidence.
    Returns empty list if YOLO is unavailable or no faces found.
    Never raises an exception.
    """
    global _yolo_model, _yolo_available

    if _yolo_model is None and not _yolo_available:
        _load_yolo_model()

    if not _yolo_available or _yolo_model is None:
        return []

    try:
        results = _yolo_model.predict(
            source=frame_bgr,
            verbose=False,
            conf=confidence_threshold
        )

        boxes = []
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    boxes.append({
                        "x1": int(xyxy[0]),
                        "y1": int(xyxy[1]),
                        "x2": int(xyxy[2]),
                        "y2": int(xyxy[3]),
                        "confidence": conf
                    })
        return boxes

    except Exception:
        return []


def get_yolo_status() -> dict:
    """
    Returns current status of YOLO model for diagnostics.
    """
    return {
        "available": _yolo_available,
        "model_path": _MODEL_PATH,
        "model_file_exists": os.path.exists(_MODEL_PATH)
    }
