# Reunite AI 2.0 — Complete System Analysis (Audit Version)

> **Document Status:** Verified Audit  
> **Date:** March 10, 2026  
> **Scope:** Full-stack (Backend FastAPI, Frontend React, AI Engine)

---

## 1. Project Overview & Folder Structure

Reunite AI is an AI-powered missing persons recovery system utilizing deep learning (ArcFace) to match registered cases with public sightings and CCTV footage.

### 1.1 Full Folder Structure (Actual)  
```text
.
├── backend
│   ├── api
│   │   ├── routers
│   │   │   ├── auth.py          # JWT, Login (YAML), Demo session
│   │   │   ├── cases.py         # Case Registration & Management
│   │   │   ├── matching.py      # Batch Matching & Statistics
│   │   │   ├── public.py        # Public Sighting Submissions
│   │   │   └── video.py         # CCTV Video Analysis (v2)
│   ├── pages
│   │   ├── helper
│   │   │   ├── data_models.py   # SQLModel Database Schemas
│   │   │   ├── db_queries.py    # Database CRUD & Logic
│   │   │   ├── fallback_detector.py # [PROTECTED] Pass 2 Speed logic
│   │   │   ├── match_algo.py    # Core Matching Algorithm
│   │   │   ├── model_cache.py   # [EMPTY]
│   │   │   ├── registration_encoder.py # [PROTECTED] Pass 1 Registration
│   │   │   ├── train_model.py   # Legacy/Validation stub
│   │   │   ├── utils.py         # Image/Encoding Utilities
│   │   │   └── video_processor.py # CCTV Processing Orchestrator
│   ├── resources/               # Storage for uploaded case/sighting photos
│   ├── video_uploads/           # Storage for uploaded CCTV videos
│   ├── main.py                  # Entry Point, CORS, Router mounting
│   ├── test_registration.py     # [PROTECTED] Self-test for registration
│   └── test_speed.py            # [PROTECTED] Self-test for video speed
├── frontend
│   ├── src
│   │   ├── app
│   │   │   ├── components/      # UI, Layouts, Protected Routes
│   │   │   ├── context/         # AuthContext (JWT management)
│   │   │   ├── pages/
│   │   │   │   ├── auth/        # Login, Signup, Forgot Password
│   │   │   │   ├── dashboard/   # 7 Core Dashboard Pages
│   │   │   │   └── LandingPage.tsx
│   │   │   ├── services/
│   │   │   │   └── api.ts       # Centralized API Service (Axios-like)
│   │   │   └── App.tsx          # React Router & Core Structure
│   └── ...
└── docs/
    └── SYSTEM_ANALYSIS.md       # THIS DOCUMENT
```

---

## 2. Backend Deep Dive

### 2.1 API Routers (`backend/api/routers/`)

#### `auth.py`
*   **Purpose:** Manages user sessions and JWT tokens.
*   **Constants:** `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.
*   **Functions:**
    *   `create_access_token()`: Generates JWT for authenticated users.
    *   `verify_yaml_credentials()`: Validates against `login_config.yml`.
    *   `login()`: `POST /auth/login` - Authenticates user.
    *   `signup()`: `POST /auth/signup` - **[NON-PERSISTENT]** Creates a session/token but does not save to DB.
    *   `get_current_user()`: Placeholder for token verification.

#### `cases.py`
*   **Purpose:** Handles missing person registration.
*   **Constants:** `RESOURCES_DIR`.
*   **Functions:**
    *   `extract_face_encoding_from_image()`: Delegates to `registration_encoder.py`.
    *   `register_case()`: `POST /cases` - Saves photo, extracts embedding, triggers background matching.
    *   `list_cases()`: `GET /cases` - Filters by status (default "NF").
    *   `get_case()`: `GET /cases/{id}`.
    *   `mark_as_found()`: `PATCH /cases/{id}/found`.
    *   `delete_case()`: `DELETE /cases/{id}` - Also removes photo from filesystem.

#### `public.py`
*   **Purpose:** Handles public sighting submissions.
*   **Functions:**
    *   `submit_sighting()`: `POST /public` - Saves sighting, extracts embedding locally via `DeepFace`, triggers match.
    *   `list_submissions()`: `GET /public`.
    *   `delete_submission()`: `DELETE /public/{id}`.

#### `matching.py`
*   **Purpose:** Statistical dashboard and manual matching control.
*   **Functions:**
    *   `run_matching_task()`: `POST /matching/run` - Triggers `match_algo.py` batch.
    *   `confirm_match()`: `POST /matching/confirm` - Links a sighting to a case and marks both FOUND.
    *   `get_stats()`: `GET /statistics` - Aggregated counts for dashboard.
    *   `get_recent_matches()`: `GET /matches` - Returns cases with `matched_with` set but status "NF".

#### `video.py`
*   **Purpose:** Phase 2 CCTV Analysis (v2).
*   **Functions:**
    *   `upload_video()`: `POST /video/upload` - Validates video and triggers `video_processor.py` in background.
    *   `get_status()`: `GET /video/status/{id}` - Progress tracking.
    *   `get_results()`: `GET /video/results/{case_id}` - Fetch AI sightings from video.

### 2.2 Helper Modules (`backend/pages/helper/`)

#### `video_processor.py`
*   **Core Logic:** Implements the **Two-Pass Video System**.
    *   **Pass 1:** Strict thresholds (`0.40`), `retinaface` backend.
    *   **Pass 2 (Fallback):** Triggered if Pass 1 finds 0 faces. Uses logic from `fallback_detector.py`.
*   **Constants:** `FRAME_INTERVAL_SECONDS`, `DEFAULT_CONFIDENCE_THRESHOLD`, `SUPPRESSION_WINDOW_SEC`.
*   **Functions:**
    *   `process_video()`: Main loop with frame seeking and 5-layer deduplication.
    *   `_detect_and_embed()`: Face detection wrapper.
    *   `_has_faces_fast()`: Haar Cascade pre-filter for speed.

#### `registration_encoder.py` [PROTECTED]
*   **Purpose:** The single source of truth for case registration embeddings.
*   **Critical Rule:** Uses `ArcFace` + `retinaface` with `enforce_detection=True`. NO preprocessing allowed.

#### `fallback_detector.py` [PROTECTED]
*   **Purpose:** Highly optimized face detection for the fallback pass (Pass 2).
*   **Critical Rule:** Uses `opencv` backend for extreme speed and relaxed thresholds.

#### `match_algo.py`
*   **Purpose:** Mathematical comparison of 512-dim embeddings.
*   **Functions:**
    *   `match_one_against_all()`: Incremental matching used after every new registration.
    *   `match()`: Batch all-vs-all matching.
    *   `calculate_cosine_distance()`: Core metric.

---

## 3. Frontend Deep Dive

### 3.1 Services (`api.ts`)
*   **Centralized Client:** Uses `fetch` with `localStorage` token injection.
*   **Endpoints:** Mirrors all backend routers (Auth, Cases, Public, Matching, Video).
*   **Base URL:** `http://127.0.0.1:8000/api/v1` (v1) and `/api/v2` (video).

### 3.2 Pages (`dashboard/`)
*   **`Home.tsx`**: Dashboard with statistics cards and "Recently Added" case list.
*   **`RegisterCase.tsx`**: 4-step wizard (Photo → Details → Reporter → Review). Maps frontend fields to backend `FormData`.
*   **`VideoAnalysis.tsx`**: Multi-phase CCTV tool (Upload → Polling → Timeline Results).
*   **`MatchCases.tsx`**: Triggers manual match scan; displays side-by-side comparisons of potential matches.
*   **`MobileApp.tsx`**: Simulated public interface for browsing missing people and submitting sightings.
*   **`AllCases.tsx` / `PublicSightings.tsx`**: Data tables for record management.

---

## 4. Database Models (`data_models.py`)

| Table | Primary Columns | Purpose |
|---|---|---|
| `RegisteredCases` | `id`, `name`, `face_mesh`, `status`, `matched_with` | Missing persons database |
| `PublicSubmissions`| `id`, `location`, `mobile`, `face_mesh`, `status` | Citizen sightings |
| `VideoUploads` | `file_path`, `status`, `processed_frames`, `used_fallback` | CCTV job tracking |
| `VideoDetections` | `timestamp_seconds`, `confidence`, `cropped_face_path` | AI results from video |

---

## 5. System Flows

### 5.1 Registration Flow
1. User uploads photo in `RegisterCase.tsx`.
2. Backend `cases.py` calls `registration_encoder.py` (Pass 1).
3. If face found: Record saved to `RegisteredCases` with JSON embedding.
4. `BackgroundTasks` triggered: `match_one_against_all` compares new case vs all public sightings.

### 5.2 Video Processing Flow (Two-Pass)
1. Video uploaded via `VideoAnalysis.tsx`.
2. `video_processor.py` starts **Pass 1** (Strict).
3. If **Pass 1** yields **ZERO** results AND `used_fallback=False`:
    *   **Pass 2** starts: Uses `fallback_detector.py` (Fast `opencv` backend, relaxed thresholds).
4. Results deduplicated (Time/Similarity) and saved to `VideoDetections`.

---

## 6. Technical Debt & Known Issues

### 6.1 Critical Mismatches
1.  **Auth Non-Persistence:** The `/signup` endpoint in `auth.py` does not save user records to a database. Restarting the backend loses all signed-up users.
2.  **Terminology (face_recognition vs DeepFace):** Multiple comments in `match_algo.py` and `train_model.py` reference the `face_recognition` library, but the actual implementation uses `DeepFace`.
3.  **Mock Tracking:** `MobileApp.tsx` contains a "Track Status" tab which is a pure UI mock; there is no backend endpoint to query a sighting by reference ID.

### 6.2 Code Oddities
*   **`model_cache.py`**: Exists as an empty file, imported nowhere but potentially intended for future speed optimizations.
*   **`train_model.py`**: The `train()` function is a misnomer; it only checks if data exists (validation) because ArcFace uses pre-trained models.
*   **Duplicated Encoding logic:** While `cases.py` is protected, `public.py` still contains its own `DeepFace` extraction logic instead of using a unified helper.

### 6.3 Missing Connections
*   **FIR Integration:** The frontend collects FIR details in `RegisterCase.tsx`, but these are flattened into the `last_seen` string or discarded in the backend `RegisteredCases` model.
*   **Notification System:** Front-end mentions "You will be notified," but there is no email/SMS/Push notification engine connected in the backend.

---
**END OF ANALYSIS**
