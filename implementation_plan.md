# Implementation Plan - System-Level Debugging & Architecture Fixes

**Goal**: Resolve slow loading, "no match found" errors, and data inconsistencies by restructuring the matching logic and enforcing data integrity.

## User Review Required

> [!IMPORTANT]
> **Blocking Change**: The "Match Cases" page will no longer run the matching algorithm every time it loads. Instead, it will display *stored* matches. Users must click a "Scan for New Matches" button to trigger a fresh scan if needed, or rely on the automatic background matching upon submission.

> [!WARNING]
> **Data Cleanup**: A script will be provided to identify and remove/flag existing cases with "Zero Vectors" (invalid face encodings). These cases are currently unmatchable and clutter the database.

## Proposed Changes

### Backend

#### [MODIFY] [match_algo.py](file:///C:/Users/tirth/OneDrive/Desktop/Reunite%20AI%201.5/backend/pages/helper/match_algo.py)
- Refactor `match()` to accept specific `case_id` (Incremental Matching).
- Implement `match_one_against_all(case_id, type="public"|"registered")`.
- Optimize internal loops to avoid re-parsing JSON for every comparison.

#### [MODIFY] [matching.py](file:///C:/Users/tirth/OneDrive/Desktop/Reunite%20AI%201.5/backend/api/routers/matching.py)
- Update `run_matching` endpoint to support optional `limit` or `case_id`.
- Ensure it uses the optimized matching logic.

#### [MODIFY] [cases.py](file:///C:/Users/tirth/OneDrive/Desktop/Reunite%20AI%201.5/backend/api/routers/cases.py) & [public.py](file:///C:/Users/tirth/OneDrive/Desktop/Reunite%20AI%201.5/backend/api/routers/public.py)
- **Validation**: Throw `HTTPException(400, detail="No face detected")` if `DeepFace` returns zero vector.
- **Async Trigger**: Use `BackgroundTasks` to call `match_one_against_all(case_id)` immediately after saving. This ensures data is "pre-matched" for the dashboard.
- **Mobile Integration**: Expose an endpoint `POST /public/sighting` that the mobile app can call, ensuring the same validation logic is applied.

#### [NEW] [fix_zero_vectors.py](file:///C:/Users/tirth/OneDrive/Desktop/Reunite%20AI%201.5/backend/fix_zero_vectors.py)
- Script to scan DB for cases with `[0.0, 0.0,...]` encodings.
- Re-process image if present, else mark as invalid.

### Mobile App (Streamlit)

#### [MODIFY] [mobile_app.py](file:///C:/Users/tirth/OneDrive/Desktop/Reunite%20AI%201.5/backend/mobile_app.py)
- **Critical Fix**: Stop direct DB insertion.
- **New Flow**: Send image to `POST /api/v1/public` (backend) via `requests` library. This ensures validation and matching logic is shared.

### Deployment Preparation

#### [NEW] [Dockerfile](file:///C:/Users/tirth/OneDrive/Desktop/Reunite%20AI%201.5/Dockerfile)
- Multi-stage build for Backend (Python) + Frontend (Vite Build).
- Production runner using `uvicorn` and serving static frontend files.

#### [NEW] [supervisord.conf](file:///C:/Users/tirth/OneDrive/Desktop/Reunite%20AI%201.5/supervisord.conf)
- Configuration to run both Backend API and Streamlit App in a single container for easy deployment (optional but recommended for free tier).

## Verification Plan

### Automated Tests
- None existing.
- I will create a test script `test_matching_flow.py` that:
    1.  Submits a case (mocked or real).
    2.  Verifies background task trigger (if possible) or calls the match function manually.
    3.  Checks DB for match record.

### Manual Verification
1.  **Zero-Vector Check**: Upload an image with no face (e.g., a black square). Verify API returns error "No face detected".
2.  **Match Flow**:
    -   Upload Person A to "Registered Cases".
    -   Upload Person A to "Public Sightings".
    -   Wait 5 seconds.
    -   Check "Matches" page. The match should appear *without* clicking "Run Matching".
3.  **Performance**:
    -   Measure time to load "Matches" page (should be instant as it fetches DB records).
    -   Measure time to "Submit Case" (should not increase significantly).
