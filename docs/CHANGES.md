# Recent Changes (Past 2 Weeks)

## March 10, 2026 - Fixing Video Processing Speed & Analyzing Recent Changes
**Files Modified:**
- `backend/pages/helper/fallback_detector.py` [NEW]
- `backend/pages/helper/video_processor.py`
- `backend/test_speed.py` [NEW]

**What was changed and why:**
Resolved speed regressions in the video processing fallback pass. The logic was isolated into a new protected file (`fallback_detector.py`) to enforce strict speed targets (under 50ms per frame) and prevent future regressions. A new test script `test_speed.py` was created to self-test processing speed. Redundant constants were removed from `video_processor.py`.

**Constants, Functions, and Imports:**
- **Added Functions:** `get_fallback_frame_interval`, `has_face_loose`, `upscale_if_small`, `detect_face_fallback`, `apply_clahe` (in `fallback_detector.py`)
- **Added Constants:** `FALLBACK_DETECTOR_BACKEND`, `FALLBACK_ENFORCE_DETECTION`, `FALLBACK_ALIGN`, `FALLBACK_MODEL`, `FALLBACK_DISTANCE_THRESHOLD`, `FALLBACK_MIN_CONFIDENCE`, `FALLBACK_INTERVAL_SHORT` etc.
- **Removed Constants:** Redundant fallback-specific constants in `video_processor.py` were removed.

## March 9, 2026 - Hardening Registration Flow
**Files Modified:**
- `backend/pages/helper/registration_encoder.py` [NEW]
- `backend/api/routers/cases.py`
- `backend/test_registration.py` [NEW]

**What was changed and why:**
Made the case registration face extraction function permanently unbreakable to prevent future modifications from breaking it. Face embedding extraction logic was isolated to a protected file (`registration_encoder.py`). `cases.py` was updated to delegate to this new module, and a self-test script (`test_registration.py`) was added.

**Constants, Functions, and Imports:**
- **Added Functions:** `extract_registration_embedding`
- **Imports Added:** `deepface.DeepFace`, `cv2`, `numpy` isolated in encoder.

## March 9, 2026 - Video Processor Refactor
**Files Modified:**
- `backend/pages/helper/video_processor.py`

**What was changed and why:**
Refactored the video processing pipeline to improve performance and accuracy. Replaced multi-backend retries with a single fast backend in the fallback pass. Restored the lightweight Haar cascade pre-filter with looser parameters. Adapted frame sampling and upscaled small face regions. This resolved issues with detecting faces in challenging conditions but introduced speed regressions that had to be fixed on Mar 10.

## March 9, 2026 - Fixing Registration & Fallback
**Files Modified:**
- `backend/api/routers/cases.py`
- `backend/pages/helper/video_processor.py`
- `backend/pages/helper/db_queries.py`

**What was changed and why:**
Fixed the broken photo registration pipeline by removing faulty preprocessing steps. Ensured `extract_face_encoding_from_image` strictly adhered to specifications. Enhanced the video processing fallback pass by adding a new preprocessing function and logic to re-extract embeddings using multiple backends. Added query functions in DB layer.

**Constants, Functions, and Imports:**
- **Added Functions:** `_preprocess_for_fallback`, `_extract_fallback_embedding` (in `video_processor.py`), `get_case_photo_path` (in `db_queries.py`).

## March 9, 2026 - Fixing Fallback Pass & CORS Policy Block
**Files Modified:**
- `backend/main.py` & `api/routers/...` (CORS policies)
- `backend/pages/helper/video_processor.py`

**What was changed and why:**
- **CORS Block:** Updated backend to resolve CORS policy errors blocking frontend v2 API requests.
- **Fallback Pass:** Improved accuracy of fallback detection by adjusting confidence thresholds, safely disabling the Haar cascade pre-filter (which was breaking detections), and relaxing face size checks. This broke speeds and was later reverted to use a looser Haar cascade algorithm.

## March 8, 2026 - Cleaning Streamlit References & General Updates
**Files Modified:**
- `SYSTEM_ANALYSIS.md`
- `system_flowcharts.md`
- Core project files (Feb 26 - Mar 8 commit)

**What was changed and why:**
Replaced outdated Streamlit documentation with React and FastAPI architecture details. Merged in global project updates including the 5-layer deduplication logic.

**Constants, Functions, and Imports:**
- **Added Functions:** `mark_case_as_found`, `ensure_video_detections_index`, `_get_haar_cascade`, `_has_faces_fast`, `_format_timestamp`
- **Added Constants:** `RESOURCES_DIR`, `MIN_CONFIDENCE_PERCENT`, `SUPPRESSION_WINDOW_SEC`, `SUPPRESSION_SIMILARITY`

## March 1, 2026 - Fixing Low Confidence Detections
**Files Modified:**
- `backend/pages/helper/video_processor.py`

**What was changed and why:**
Implemented strict logic to reject detections below 60% confidence (cosine distance > 0.40) to prevent false positives in video processing.

## February 27, 2026 - Implementing 5-Layer Dedup & Phase 2 Analysis
**Files Modified:**
- `backend/pages/helper/video_processor.py`
- `backend/pages/helper/data_models.py`
- `backend/pages/helper/db_queries.py`
- `README.md` and Phase 2 docs.

**What was changed and why:**
Resolved duplicate detection entries being stored. Added timestamp-level deduplication, consecutive frame suppression, and a unique DB constraint.

---

### Analysis of Breakages & Regressions

**Things that were working before but broke after a later change:**
1. **Photo Registration:** Breakages occurred after faulty preprocessing steps were added to improving the model (likely during earlier deepface optimization phases). This had to be fixed on Mar 9 by completely removing the preprocessing and isolating the `registration_encoder.py`.
2. **Video Processing Speed:** On Mar 9, multi-backend re-extraction and retry loops were added to the fallback pass to catch missed faces, which caused a massive speed regression. This was working fast before, but broke speed targets. On Mar 10, this was ripped out into `fallback_detector.py` to restore single-call OpenCV speed.
3. **Haar Cascade Pre-filtering:** Initially added in late Feb/early Mar to skip empty frames aggressively, which broke difficult low-light/angled face detections (since OpenCV Haar cascade is strict). It was disabled on Mar 9 to fix accuracy, but this tanked performance since DeepFace was running on empty frames. It was subsequently restored later on Mar 9 with "looser parameters" (using `haarcascade_profileface`) to balance speed and accuracy.

**Patterns of Recurring Breakage:**
- **`video_processor.py` is a massive hotspot:** This file has been modified in almost every session over the past two weeks. The changes keep alternating between prioritizing **accuracy** and prioritizing **speed**. Features like Haar cascade filtering and confidence thresholds were toggled back and forth across different sessions (Mar 1 -> Mar 9 -> Mar 10).
- The solution to this recurring pattern of breaking `video_processor.py` was finally establishing **protected isolation files** (`fallback_detector.py` and `registration_encoder.py`) with strict non-modification rules at the top, effectively stopping changes from altering working logic in the future.
