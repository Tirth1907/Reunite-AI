import os
import re

file_path = "C:/Users/tirth/OneDrive/Desktop/Reunite AI 2.0/backend/pages/helper/video_processor.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add imports and protection comment
imports_str = """from pages.helper.data_models import VideoDetections
from pages.helper.fallback_detector import (
    detect_face_fallback,
    has_face_loose,
    upscale_if_small,
    apply_clahe,
    get_fallback_frame_interval,
    FALLBACK_DISTANCE_THRESHOLD,
    FALLBACK_MIN_CONFIDENCE,
    FALLBACK_MIN_FACE_SIZE,
    FALLBACK_MIN_EMBEDDING_NORM
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
# ============================================================"""
content = content.replace("from pages.helper.data_models import VideoDetections", imports_str)

# 2. Remove redundant fallback constants
content = re.sub(
    r"# Fallback thresholds for Pass 2 \(relaxed[^\n]+\nFALLBACK_CONFIDENCE_THRESHOLD:\s*float\s*=\s*[0-9.]+\nFALLBACK_MIN_CONFIDENCE_PERCENT:\s*int\s*=\s*[0-9]+",
    "",
    content
)

# 3. Delete redundant fallback functions
defs_to_remove = [
    r"def _has_faces_loose\([^)]*\)\s*->\s*bool:[\s\S]*?(?=def\s|\Z)",
    r"def _preprocess_for_fallback\([^)]*\)\s*->\s*np\.ndarray:[\s\S]*?(?=def\s|\Z)",
    r"def _upscale_face_region\([^)]*\)\s*->\s*np\.ndarray:[\s\S]*?(?=def\s|\Z)",
    r"def _extract_fallback_embedding\([^)]*\)\s*->\s*list\s*\|\s*None:[\s\S]*?(?=def\s|\Z)",
    r"def _detect_and_embed_fallback\([^)]*\):[\s\S]*?(?=def\s|\Z)"
]
for pattern in defs_to_remove:
    content = re.sub(pattern, "", content)

# 4. Replace _detect_and_embed size parameters
content = content.replace(
    "min_face_size = 8 if is_fallback_pass else 15",
    "min_face_size = FALLBACK_MIN_FACE_SIZE if is_fallback_pass else 15"
)
content = content.replace(
    "min_norm = 0.3 if is_fallback_pass else 1.0",
    "min_norm = FALLBACK_MIN_EMBEDDING_NORM if is_fallback_pass else 1.0"
)

# 5. Fix _run_processing_pass interval calculation
content = content.replace(
    "interval_seconds = get_adaptive_frame_interval(duration_sec, is_fallback_pass)",
    "interval_seconds = get_fallback_frame_interval(duration_sec) if is_fallback_pass else get_adaptive_frame_interval(duration_sec, is_fallback_pass)"
)

# 6. Delete fallback re-extraction block
content = re.sub(
    r"\s*# ---- Fallback: re-extract target embedding with optimized settings ----[\s\S]*?for frame_idx, timestamp_sec in enumerate\(extraction_times\):",
    "\n\n        for frame_idx, timestamp_sec in enumerate(extraction_times):",
    content
)

# 7. Replace pre-filter logic in fallback
content = content.replace(
    "if not _has_faces_loose(frame_bgr):",
    "if not has_face_loose(frame_bgr):"
)

# 8. Replace CLAHE and detect calls
content = content.replace(
    "frame_rgb = _preprocess_for_fallback(frame_rgb)",
    "frame_rgb = apply_clahe(frame_rgb)"
)
content = content.replace(
    "fallback_results = _detect_and_embed_fallback(frame_rgb, enforce_detection=False)",
    "fallback_results = detect_face_fallback(frame_rgb)"
)

# 9. Update process_video call
content = content.replace(
    "confidence_threshold=FALLBACK_CONFIDENCE_THRESHOLD",
    "confidence_threshold=FALLBACK_DISTANCE_THRESHOLD"
).replace(
    "min_confidence_percent=FALLBACK_MIN_CONFIDENCE_PERCENT",
    "min_confidence_percent=FALLBACK_MIN_CONFIDENCE"
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
