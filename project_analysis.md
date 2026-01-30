# Project Analysis: Reunite AI 1.5

## 1. Project Overview
**Reunite AI 1.5** is a full-stack web and mobile application designed to help find missing persons using AI-powered face recognition.

### Tech Stack
- **Backend**: FastAPI (Python), SQLite (Database), DeepFace (AI/ML for Face Recognition).
- **Frontend**: React (Vite, TypeScript), TailwindCSS (Styling).
- **Mobile/Public Portal**: Streamlit (Python-based web app acting as a mobile interface).
- **Storage**: Local filesystem (`/resources` folder) for images; SQLite for metadata.

## 2. Architecture & Data Flow

### Components
1.  **FastAPI Server (`backend/main.py`)**: The core logic hub. Handles Auth, Case Management, and Matching.
2.  **React Frontend (`frontend/`)**: The dashboard for authorities/admin to manage cases and view matches.
3.  **Streamlit App (`backend/mobile_app.py`)**: A public-facing simplified interface for citizens to upload sightings. **CRITICAL INFO**: This app currently connects *directly* to the SQLite database and bypasses the FastAPI backend application logic.

### Data Flow Traces

#### A. Case Registration (Admin)
1.  **Frontend**: User submits form + photo via `POST /api/v1/cases`.
2.  **Backend (`cases.py`)**:
    -   Saves image to `resources/`.
    -   Extracts face encoding (Synchronous `DeepFace.represent` or threaded).
    -   **Issue**: If no face found, saves `[0,0,...]` vector.
    -   Saves metadata + encoding to SQLite `RegisteredCases`.

#### B. Public Sighting (Mobile/Streamlit)
1.  **Streamlit App**: User uploads photo.
2.  **Logic (`mobile_app.py`)**:
    -   Extracts encoding using `utils.py` (which uses `DeepFace`).
    -   Directly inserts into `PublicSubmissions` table in SQLite.
    -   **CRITICAL FLAW**: Does *not* trigger the matching algorithm.

#### C. Matching Logic (The Bottleneck)
1.  **Frontend**: User visits "Match Cases" page -> calls `runMatching()`.
2.  **Backend (`matching.py`)**:
    -   Fetches ALL public cases.
    -   Fetches ALL registered cases.
    -   Loops O(N*M) to compare every pair.
    -   Updates `matched_with` column in DB.
    -   Returns results.
3.  **Result**: Extreme slowness as database grows.

## 3. Root Cause Analysis (Confirmed)

| Reported Problem | Root Cause |
| :--- | :--- |
| **Very long loading time** | The "Match Cases" page triggers the O(N*M) matching algorithm synchronously on load. It re-calculates everything instead of just fetching results. |
| **"No match found"** | 1. **Zero Vectors**: Images with no detected face are saved as all-zeros, which never match.<br>2. **Threshold**: The strict tolerance (0.5/0.6) might be too high for low-quality photos. |
| **Inconsistent Behavior** | The **Mobile App (Streamlit)** acts independently. It inserts data into the DB but never triggers the API's matching logic. A sighting submitted via Mobile sits "dormant" until someone manually runs the matcher on the Web. |

## 4. Deployment Strategy

### Constraints
- **DeepFace**: Requires significant RAM and CPU. Free tiers on Render/Railway might OOM (Out of Memory) if not careful.
- **SQLite**: requires a *persistent volume*. Free tiers often have ephemeral filesystems (data verifies on restart).

### Recommended Platforms (Free/Cheap)

| Component | Platform | Configuration Notes |
| :--- | :--- | :--- |
| **Frontend** | **Vercel** | - Build Command: `npm run build`<br>- Output Dir: `dist`<br>- **Must** update `api.ts` to point to the production backend URL. |
| **Backend** | **Render (Web Service)** | - **Docker is best**. Create a `Dockerfile`.<br>- **Disk**: Free tier does NOT support persistent disks. **CRITICAL**: SQLite will be reset on deployment/restart if not using a persistent volume (paid).<br>- *Alternative for Free Tier*: Use **Supabase** (PostgreSQL) instead of SQLite, or accept data loss on restart for demo purposes. |

### Deployment Plan
1.  **Containerization**: Create a `Dockerfile` for the backend.
2.  **Environment Variables**: exact URL configuration.
3.  **Database Migration**: For a *true* production fix, we must migrate SQLite -> PostgreSQL (Supabase/Neon) to allow ephemeral deployments (like Render Free Tier). *However, for this task, I will stick to SQLite but warn about persistence.*

## 5. Proposed Fixes (Stabilization Phase)

1.  **Backend**:
    -   Create `trigger_match_background(case_id)` to run matching *after* submission.
    -   Fix "Zero Vector" bug: reject images with no faces.
2.  **Frontend**:
    -   Stop `MatchCases.tsx` from auto-running matching.
    -   Add strictly manual "Scan" button.
3.  **Mobile/Streamlit**:
    -   Modify `mobile_app.py` to call the *Backend API* instead of touching the DB directly (if possible), OR at least use the shared logic correctly.
