# ============================================================
# FALLBACK DETECTOR — DO NOT MODIFY THIS FILE
# ============================================================
# This file controls how the fallback pass detects faces in video.
# It is intentionally isolated to prevent speed regressions.
#
# CRITICAL RULES FOR ANY FUTURE CODE CHANGES:
# 1. Do NOT change FALLBACK_DETECTOR_BACKEND from "opencv"
# 2. Do NOT add retry loops or multiple backend attempts
# 3. Do NOT change enforce_detection — it must stay False
# 4. Do NOT replace detect_face_fallback() with retinaface calls
# 5. Do NOT add preprocessing that slows down per-frame processing
# 6. The fallback pass must process each frame in under 50ms
# 7. Pass 1 (CCTV mode) uses retinaface — that is correct for Pass 1
#    Do NOT apply Pass 1 settings to the fallback pass
#
# SPEED TARGETS (must never be exceeded):
#   Per frame processing time: < 50ms
#   1m33s video (93 frames): < 2 minutes total
#   5 minute video: < 4 minutes total
#   15 minute video: < 10 minutes total
#
# If you need to improve fallback detection quality:
#   - Adjust MIN_FACE_SIZE or CONFIDENCE_THRESHOLD below
#   - Do NOT change the backend or add retry loops
# ============================================================

import cv2
import numpy as np
from deepface import DeepFace

# ── FALLBACK CONSTANTS ──────────────────────────────────────
# DO NOT CHANGE FALLBACK_DETECTOR_BACKEND
FALLBACK_DETECTOR_BACKEND = "opencv"   # fast: ~30ms vs retinaface ~400ms
FALLBACK_ENFORCE_DETECTION = False     # never raise on empty frames
FALLBACK_ALIGN = True                  # keep alignment for accuracy
FALLBACK_MODEL = "ArcFace"             # same model as Pass 1

# Confidence thresholds for fallback pass
FALLBACK_DISTANCE_THRESHOLD = 0.65    # cosine distance (relaxed)
FALLBACK_MIN_CONFIDENCE = 35          # percent (relaxed)

# Frame sampling intervals for fallback pass (seconds)
# Denser than Pass 1 to maximize detection chances
FALLBACK_INTERVAL_SHORT = 1           # videos under 90 seconds
FALLBACK_INTERVAL_MEDIUM = 2          # 90s to 5 minutes
FALLBACK_INTERVAL_LONG = 4            # 5 to 10 minutes
FALLBACK_INTERVAL_VLONG = 6           # 10 to 15 minutes
FALLBACK_INTERVAL_MAX = 10            # over 15 minutes

# Face quality minimums for fallback (relaxed vs Pass 1)
FALLBACK_MIN_FACE_SIZE = 8            # pixels (Pass 1 uses 15)
FALLBACK_MIN_EMBEDDING_NORM = 0.3     # (Pass 1 uses 1.0)
FALLBACK_MIN_UPSCALE_SIZE = 80        # upscale faces smaller than this
# ────────────────────────────────────────────────────────────


def get_fallback_frame_interval(duration_seconds: float) -> int:
    """
    Returns frame extraction interval for fallback pass.
    Uses denser sampling than Pass 1 for better detection.
    DO NOT MODIFY — controls processing speed balance.
    """
    if duration_seconds <= 93:
        return FALLBACK_INTERVAL_SHORT
    elif duration_seconds <= 300:
        return FALLBACK_INTERVAL_MEDIUM
    elif duration_seconds <= 600:
        return FALLBACK_INTERVAL_LONG
    elif duration_seconds <= 900:
        return FALLBACK_INTERVAL_VLONG
    else:
        return FALLBACK_INTERVAL_MAX


def has_face_loose(frame_bgr: np.ndarray) -> bool:
    """
    Fast lightweight face pre-filter for fallback pass (~5ms).
    Looser than Pass 1 Haar filter — accepts angled and small faces.
    Returns True if any face-like region found OR if filter fails.
    DO NOT REPLACE WITH DeepFace — this must stay fast.
    """
    try:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_GRAY)

        frontal = cv2.CascadeClassifier(
            cv2.data.haarcascades +
            'haarcascade_frontalface_default.xml'
        )
        faces = frontal.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=1,
            minSize=(20, 20),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        if len(faces) > 0:
            return True

        profile = cv2.CascadeClassifier(
            cv2.data.haarcascades +
            'haarcascade_profileface.xml'
        )
        profiles = profile_cascade = profile.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=1,
            minSize=(20, 20)
        )
        return len(profiles) > 0

    except Exception:
        return True  # fail open — let DeepFace decide


def upscale_if_small(img: np.ndarray) -> np.ndarray:
    """
    Upscale small face images before embedding.
    Small faces produce poor ArcFace embeddings.
    Target: minimum 80x80 pixels.
    """
    if img is None or img.size == 0:
        return img
    h, w = img.shape[:2]
    if h < FALLBACK_MIN_UPSCALE_SIZE or w < FALLBACK_MIN_UPSCALE_SIZE:
        scale = max(
            FALLBACK_MIN_UPSCALE_SIZE / h,
            FALLBACK_MIN_UPSCALE_SIZE / w
        )
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h),
                          interpolation=cv2.INTER_CUBIC)
    return img


def detect_face_fallback(frame_rgb: np.ndarray) -> list:
    """
    Single fast DeepFace call for fallback pass.
    Uses opencv backend (~30ms) NOT retinaface (~400ms).
    Makes EXACTLY ONE DeepFace call — no retries, no loops.

    DO NOT ADD RETRY LOOPS TO THIS FUNCTION.
    DO NOT CHANGE THE BACKEND TO retinaface.
    DO NOT ADD MULTIPLE BACKEND ATTEMPTS.

    Returns list of results or empty list — never raises.
    """
    if not np.any(frame_rgb):
        return []
    try:
        results = DeepFace.represent(
            img_path=frame_rgb,
            model_name=FALLBACK_MODEL,
            detector_backend=FALLBACK_DETECTOR_BACKEND,
            enforce_detection=FALLBACK_ENFORCE_DETECTION,
            align=FALLBACK_ALIGN
        )
        if results and len(results) > 0:
            return results
        return []
    except Exception:
        return []  # never raise — always return empty list


def apply_clahe(img_rgb: np.ndarray) -> np.ndarray:
    """
    Gentle contrast enhancement for dark/low-quality frames.
    Only enhances brightness — does NOT crop or resize.
    Returns original image if enhancement fails.
    """
    try:
        lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab_enhanced = cv2.merge([clahe.apply(l), a, b])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)
    except Exception:
        return img_rgb
