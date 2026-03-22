# Reunite AI — Pipeline Debug Report

## 1. _detect_and_embed Function

### Full Current Source Code

```python
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
                        faces.append((embedding, facial_area, None))
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
                # Generate base64 thumbnail from facial area
                try:
                    fx = max(0, facial_area.get("x", 0))
                    fy = max(0, facial_area.get("y", 0))
                    fw = facial_area.get("w", 0)
                    fh = facial_area.get("h", 0)
                    if fw > 0 and fh > 0:
                        face_crop = frame_rgb[fy:fy+fh, fx:fx+fw]
                        face_crop_bgr = cv2.cvtColor(face_crop, cv2.COLOR_RGB2BGR)
                        face_crop_bgr = cv2.resize(face_crop_bgr, (160, 160))
                        _, buffer = cv2.imencode(".jpg", face_crop_bgr)
                        face_b64 = base64.b64encode(buffer).decode("utf-8")
                    else:
                        face_b64 = None
                except Exception:
                    face_b64 = None
                if face_w >= 30 and face_h >= 30:
                    faces.append((embedding, facial_area, face_b64))
        return faces
    except Exception:
        return []
```

### Conditions That Can Return 0 Faces

1. **YOLO branch with empty/None boxes**: If `yolo_boxes` is `None` or empty list, falls through to OpenCV branch.
2. **YOLO box invalid geometry**: `x2 <= x1 or y2 <= y1` — box skipped.
3. **YOLO crop empty**: `face_crop.size == 0` — box skipped.
4. **YOLO DeepFace.represent throws exception**: Caught by bare `except Exception: continue` — silently skipped.
5. **YOLO no embedding returned**: `results` empty, or `results[0].get("embedding")` is None — skipped.
6. **OpenCV branch: DeepFace.represent throws exception**: Caught by outer `except Exception: return []` — returns empty, **no logging**.
7. **OpenCV branch: no results**: `if not results: return []`.
8. **OpenCV face_confidence too low**: `face_confidence < 0.50` — face skipped.
9. **OpenCV face too small**: `face_w < 30 or face_h < 30` — face skipped.

### Lines That Silently Swallow Exceptions

| Line | Code | Impact |
|------|------|--------|
| 279 | `except Exception: continue` | YOLO path: any DeepFace error silently skipped per box, no logging |
| 315-316 | `except Exception: face_b64 = None` | Thumbnail encoding failure silently absorbed |
| 320 | `except Exception: return []` | **CRITICAL**: Entire OpenCV DeepFace call failure returns 0 faces with zero logging |

---

## 2. Frame Loop Analysis

### Full Current Source Code of _run_processing_pass

```python
def _run_processing_pass(
    video_path: str,
    case_embedding,
    video_id: str,
    case_id: str,
    confidence_threshold: float,
    min_confidence_percent: int,
    is_fallback_pass: bool = False,
):
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

        if not is_fallback_pass:
            db_queries.update_video_status(
                video_id, status="processing", total_frames=total_frames_to_process
            )

        detections_buffer = []
        processed = 0
        detection_count = 0
        skipped_no_face = 0

        last_saved_timestamp = -999.0
        last_saved_embedding = None

        db_queries.ensure_video_detections_index()

        for frame_idx, timestamp_sec in enumerate(extraction_times):
            target_frame_number = int(timestamp_sec * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_number)
            ret, frame_bgr = cap.read()

            if not ret or frame_bgr is None:
                processed += 1
                continue

            h_orig, w_orig = frame_bgr.shape[:2]
            if w_orig > TARGET_MAX_WIDTH or h_orig > TARGET_MAX_HEIGHT:
                scale = min(TARGET_MAX_WIDTH / w_orig, TARGET_MAX_HEIGHT / h_orig)
                new_w = int(w_orig * scale)
                new_h = int(h_orig * scale)
                frame_bgr = cv2.resize(frame_bgr, (new_w, new_h))

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

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

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
                    faces.append((embedding, facial_area, None))
            else:
                if not _has_faces_fast(frame_rgb):
                    continue
                faces = _detect_and_embed(frame_rgb, is_fallback_pass=False)

            best_frame_match = None

            for embedding, facial_area, face_b64 in faces:
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
                        logger.info(...)
                else:
                    if distance <= confidence_threshold and confidence >= min_confidence_percent:
                        if best_frame_match is None or confidence > best_frame_match[1]:
                            best_frame_match = (distance, confidence, embedding_arr, facial_area)
                    else:
                        logger.info(...)

            if best_frame_match is not None:
                _, confidence, embedding_arr, facial_area = best_frame_match

                suppressed = False
                time_gap = timestamp_sec - last_saved_timestamp

                if time_gap < SUPPRESSION_WINDOW_SEC and last_saved_embedding is not None:
                    face_dist = _cosine_distance(last_saved_embedding, embedding_arr)
                    if face_dist < SUPPRESSION_SIMILARITY:
                        logger.info(...)
                        suppressed = True

                if not suppressed:
                    detection_id = str(uuid.uuid4())

                    detection = VideoDetections(
                        id=detection_id,
                        video_id=video_id,
                        case_id=case_id,
                        timestamp_seconds=round(timestamp_sec, 2),
                        confidence=round(confidence, 2),
                        cropped_face_path=None,
                        face_thumbnail=face_b64,
                        frame_number=frame_idx,
                        is_low_confidence=is_fallback_pass,
                    )

                    detections_buffer.append(detection)
                    detection_count += 1
                    last_saved_timestamp = timestamp_sec
                    last_saved_embedding = embedding_arr

            del frame_bgr, frame_rgb
            processed += 1

            if processed % PROGRESS_UPDATE_INTERVAL == 0:
                if detections_buffer:
                    db_queries.save_video_detections_batch(detections_buffer)
                    detections_buffer = []
                db_queries.update_video_status(...)

        if detections_buffer:
            db_queries.save_video_detections_batch(detections_buffer)
            detections_buffer = []

        return detection_count

    finally:
        cap.release()
```

### Conditions That Skip a Frame

| Condition | Line(s) | Pass |
|-----------|---------|------|
| `not ret or frame_bgr is None` | 485-487 | Both |
| `not has_face_loose(frame_bgr)` | 499-510 | Fallback only |
| `not _has_faces_fast(frame_bgr)` (Haar on BGR) | 515-528 | Pass 1 only |
| `not _has_faces_fast(frame_rgb)` (Haar on RGB, second check) | 550-551 | Pass 1 only |

### Conditions That Skip Saving a Detection

| Condition | Description |
|-----------|-------------|
| `_detect_and_embed` returns 0 faces | No faces to compare |
| `len(embedding_arr) != len(case_embedding)` | Embedding dimension mismatch |
| `distance > confidence_threshold` (Pass 1) | Not close enough match |
| `confidence < min_confidence_percent` (Pass 1) | Below confidence floor |
| `distance > FALLBACK_DISTANCE_THRESHOLD` (Pass 2) | Not close enough for fallback |
| `confidence < FALLBACK_MIN_CONFIDENCE` (Pass 2) | Below fallback confidence floor |
| Suppression: `time_gap < 3s AND face_dist < 0.10` | Dedup suppression |

### Distance Threshold Values

| Parameter | Value | Used In |
|-----------|-------|---------|
| `DEFAULT_CONFIDENCE_THRESHOLD` | 0.40 | Pass 1 (distance ≤ 0.40 → confidence ≥ 60%) |
| `MIN_CONFIDENCE_PERCENT` | 60 | Pass 1 hard floor |
| `FALLBACK_DISTANCE_THRESHOLD` | Imported from `fallback_detector.py` | Pass 2 |
| `FALLBACK_MIN_CONFIDENCE` | Imported from `fallback_detector.py` | Pass 2 |
| `SUPPRESSION_SIMILARITY` | 0.10 | Both passes |
| `SUPPRESSION_WINDOW_SEC` | 3 seconds | Both passes |

---

## 3. VideoDetections Insert

### Exact Constructor Call

```python
detection = VideoDetections(
    id=detection_id,
    video_id=video_id,
    case_id=case_id,
    timestamp_seconds=round(timestamp_sec, 2),
    confidence=round(confidence, 2),
    cropped_face_path=None,
    face_thumbnail=face_b64,
    frame_number=frame_idx,
    is_low_confidence=is_fallback_pass,
)
```

### Fields Being Passed

| Field | Value | Required in DB? |
|-------|-------|-----------------|
| `id` | `str(uuid.uuid4())` | YES (PK, NOT NULL) |
| `video_id` | From function arg | YES (NOT NULL) |
| `case_id` | From function arg | YES (NOT NULL) |
| `timestamp_seconds` | `round(timestamp_sec, 2)` | YES (NOT NULL) |
| `confidence` | `round(confidence, 2)` | YES (NOT NULL) |
| `cropped_face_path` | `None` | NO (nullable) |
| `face_thumbnail` | `face_b64` variable | NO (nullable) |
| `frame_number` | `frame_idx` (loop index) | YES (NOT NULL) |
| `is_low_confidence` | `is_fallback_pass` bool | YES (default 0) |
| `detected_at` | Auto-set via `default_factory` | YES (NOT NULL) |

### Fields That Could Cause Insert Failure

1. **`face_thumbnail` may be `None`**: When the YOLO branch is used, `face_b64` is always `None` (line 278: `faces.append((embedding, facial_area, None))`). This is not a failure per se since the column is nullable, but means YOLO-detected faces will have no thumbnail.

2. **`face_b64` variable scope issue (BUG)**: The `face_b64` variable used in the constructor at line 613 comes from the `for embedding, facial_area, face_b64 in faces:` loop at line 557. However, after the loop, the code selects `best_frame_match` which only stores `(distance, confidence, embedding_arr, facial_area)` — **NOT** `face_b64`. The `face_b64` variable used at line 613 is whatever value it had on the **last iteration** of the loop, not necessarily the value corresponding to the best match.

---

## 4. Known Issues Found

### BUG 1: `face_b64` references wrong face (CRITICAL)

**What it does wrong**: The `for` loop at line 557 iterates over all faces, tracking the best match. But `face_b64` as a loop variable retains the value from the **last iteration**, not the best-matching face. When the best match is found early in the loop but more faces are iterated after, `face_b64` will correspond to the last face checked, not the best match.

**Impact**: Thumbnails saved in the database may show the wrong face, or be `None` when a valid thumbnail existed.

**Fix**: Store `face_b64` inside `best_frame_match` tuple.

---

### BUG 2: Double Haar cascade check in Pass 1 (PERFORMANCE)

**What it does wrong**: Pass 1 runs `_has_faces_fast(frame_bgr)` at line 515 (BGR input), then immediately after converting to RGB, runs `_has_faces_fast(frame_rgb)` again at line 550. The second `_has_faces_fast` definition (line 231) uses `COLOR_RGB2GRAY`, while the first definition (line 202) uses `COLOR_BGR2GRAY`. Since the second definition **redefines** the function (Python uses the last definition), both calls actually use `COLOR_RGB2GRAY`. This means:
- The first call at line 515 passes BGR data but the function converts it with `COLOR_RGB2GRAY` — this works but produces slightly different grayscale values than intended, potentially missing faces.
- The second call at line 550 is a completely redundant check that already passed the first.

**Impact**: The first pre-filter call (line 515) receives BGR frames but the active `_has_faces_fast` function uses `COLOR_RGB2GRAY` conversion. This swaps Red and Blue channels in the grayscale conversion, which may cause Haar cascade to miss some faces. Also wastes ~3-5ms per frame on the redundant second check.

**Fix**: Remove the second `_has_faces_fast` check at line 550-551. Fix the dual function definition issue.

---

### BUG 3: `_has_faces_fast` is defined TWICE (CODE DEFECT)

**What it does wrong**: There are two definitions of `_has_faces_fast`:
- **Line 202-217**: Uses `_get_haar_cascade()` (lazy-loaded) and `COLOR_BGR2GRAY`.
- **Line 231-240**: Uses `_HAAR_CASCADE` (module-level) and `COLOR_RGB2GRAY`.

Python uses the **last definition**, so the first one is dead code. All calls to `_has_faces_fast` use the second definition which expects RGB input and uses the module-level cascade.

**Impact**: Pre-filter at line 515 passes BGR frame to a function expecting RGB. Grayscale conversion uses wrong channel weights (R and B swapped). May cause false negatives (missed faces) or false positives.

**Fix**: Remove the first definition (lines 202-217) and the associated lazy-load function `_get_haar_cascade` (lines 190-199). Ensure the remaining definition's color conversion matches the input format at each call site.

---

### BUG 4: YOLO pre-screener is imported but never used in Pass 1 (DEAD CODE)

**What it does wrong**: Lines 42-45 import `has_face_yolo` and `is_yolo_available`, and line 512 has a comment "Use YOLO pre-screener first (faster, ~15ms), fall back to Haar". However, the code at line 515 immediately calls `_has_faces_fast(frame_bgr)` (Haar) without ever calling YOLO. The `yolo_boxes` variable is set to `None` at line 514 and never updated.

**Impact**: YOLO is never used as a pre-screener. `_detect_and_embed` is always called with `yolo_boxes=None`, so the YOLO branch inside `_detect_and_embed` (lines 251-281) is dead code. All face detection falls back to OpenCV Haar + DeepFace opencv backend.

**Fix**: Either implement YOLO pre-screening as the comment suggests, or remove the dead YOLO imports and code paths.

---

### BUG 5: Fallback pass generates no thumbnails (MINOR)

**What it does wrong**: In fallback pass (line 548), faces are appended as `(embedding, facial_area, None)` — `face_b64` is always `None`. This means detections from fallback Pass 2 will never have thumbnails.

**Impact**: UI cannot display face thumbnails for fallback detections.

**Fix**: Generate a base64 thumbnail in the fallback branch similar to the OpenCV branch in `_detect_and_embed`.

---

### BUG 6: Silent exception swallowing in `_detect_and_embed` (DIAGNOSTIC)

**What it does wrong**: The outer `except Exception: return []` at line 320 catches all errors from the OpenCV DeepFace path and returns empty list with zero logging. If DeepFace fails for any reason (model loading, memory, corrupt frame), the pipeline silently produces 0 detections.

**Impact**: Makes it impossible to diagnose why detections are not being found. No error appears in logs.

**Fix**: Add `logger.exception(...)` or `logger.warning(...)` inside the except block.

---

### BUG 7: `save_video_detections_batch` can silently lose detections (MINOR)

**What it does wrong**: In `db_queries.py` line 438, the batch insert catches exceptions per-detection and calls `session.rollback()`, which rolls back all previous successful flushes in the same session. The fallback at line 448-454 also catches and passes on exceptions.

**Impact**: If any single detection in a batch triggers a constraint violation, all unflushed detections in that session are lost. The individual fallback may also silently fail.

**Fix**: Use individual sessions per detection, or restructure to properly handle partial failures.

---

### ISSUE 8: Unused import `PIL.Image` (CLEANUP)

**What it does wrong**: Line 27 imports `PIL.Image` but it is never used anywhere in the file.

**Fix**: Remove the import.

---

### ISSUE 9: Unused imports `has_face_yolo`, `is_yolo_available`, `upscale_if_small` (CLEANUP)

**What it does wrong**: These are imported but never called.

**Fix**: Remove unused imports.

---

## 5. Recommended Fixes

### Fix 1: Store `face_b64` in `best_frame_match` tuple

**Before:**
```python
best_frame_match = None  # (distance, confidence, embedding_arr, facial_area)

for embedding, facial_area, face_b64 in faces:
    # ...
    if best_frame_match is None or confidence > best_frame_match[1]:
        best_frame_match = (distance, confidence, embedding_arr, facial_area)

if best_frame_match is not None:
    _, confidence, embedding_arr, facial_area = best_frame_match
    # ...
    face_thumbnail=face_b64,  # BUG: uses last loop iteration's face_b64
```

**After:**
```python
best_frame_match = None  # (distance, confidence, embedding_arr, facial_area, face_b64)

for embedding, facial_area, face_b64 in faces:
    # ...
    if best_frame_match is None or confidence > best_frame_match[1]:
        best_frame_match = (distance, confidence, embedding_arr, facial_area, face_b64)

if best_frame_match is not None:
    _, confidence, embedding_arr, facial_area, face_b64 = best_frame_match
    # ...
    face_thumbnail=face_b64,  # FIXED: uses best match's face_b64
```

---

### Fix 2: Remove duplicate `_has_faces_fast` and redundant second call

**Before:**
```python
# Lines 202-217: First definition (dead code)
def _has_faces_fast(frame_bgr):
    cascade = _get_haar_cascade()
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    ...

# Lines 231-240: Second definition (active)
def _has_faces_fast(frame_rgb) -> bool:
    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
    ...

# Line 515: First check in loop (BGR input)
face_detected = _has_faces_fast(frame_bgr)

# Line 550: Second check in loop (RGB input, redundant)
if not _has_faces_fast(frame_rgb):
    continue
```

**After:**
```python
# Keep ONE definition that handles BGR (since pre-filter receives BGR)
def _has_faces_fast(frame_bgr) -> bool:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = _HAAR_CASCADE.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60),
    )
    return len(faces) > 0

# Line 515: Keep this check
face_detected = _has_faces_fast(frame_bgr)

# Line 550-551: REMOVE this redundant second check
```

---

### Fix 3: Add logging to silent exception handler

**Before:**
```python
    except Exception:
        return []
```

**After:**
```python
    except Exception as e:
        logger.warning(f"[VIDEO] _detect_and_embed failed: {e}")
        return []
```

---

### Fix 4: Remove unused imports

**Before:**
```python
import PIL.Image

from pages.helper.yolo_prescreener import (
    has_face_yolo,
    is_yolo_available,
)
```

**After:**
```python
# Remove PIL.Image import entirely
# Remove yolo_prescreener imports if YOLO is not being used
```

---

### Fix 5: Remove dead code

Remove lines 190-217 (first `_has_faces_fast` definition and `_get_haar_cascade` lazy loader), since the second definition at lines 231-240 is the one Python actually uses.
