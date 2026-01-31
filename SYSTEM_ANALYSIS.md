# Reunite AI v1.5 - System Analysis & Technical Documentation

> [!NOTE]
> This document provides a deep technical and functional analysis of the Reunite AI v1.5 project. It is structured to serve as project documentation and as a basis for academic research papers.

## 1. Complete System Analysis

Reunite AI v1.5 is a full-stack web application designed to aid the recovery of missing persons using AI-based face matching. The system transitions from a prototype (Streamlit) to a scalable architecture (FastAPI + React).

### Major Components

#### A. Frontend (React + TypeScript)
- **Role**: Provides the user interface for Admins (Police/NGOs) and the Public.
- **Location**: `frontend/src/app`
- **Key Modules**:
    - **Dashboard (Admin)**: `RegisterCase.tsx`, `MatchCases.tsx`, `AllCases.tsx`. Allows officials to register missing persons, view auto-detected matches, and manage case statuses.
    - **Mobile App (Public)**: `MobileApp.tsx`. A responsive web-view for the public to browse missing cases (`NF`) and submit sightings anonymously.
    - **Authentication**: JWT-based login for admins.
- **Interaction**: Consumes REST APIs provided by the backend to fetch data, upload images, and trigger AI matching.

#### B. Backend (FastAPI)
- **Role**: Acts as the central orchestrator, handling API requests, business logic, and database operations.
- **Location**: `backend/`
- **Key Files**:
    - `main.py`: Application entry point; initializes API routers, CORS, and database.
    - `api/routers/`: Splits logic into `cases.py` (Admin CRUD), `public.py` (Public Sightings), `auth.py` (Login), and `matching.py` (AI verification).
- **Concurrency**: Uses `BackgroundTasks` to run heavy AI face matching operations asynchronously without blocking API responses.

#### C. AI Module (Face Matching)
- **Library**: `DeepFace` (Facebook's Deep Learning library for Python).
- **Algorithm**: **ArcFace** (chosen for high accuracy in identifying faces).
- **Logic Location**: `backend/pages/helper/match_algo.py`
- **Workflow**:
    1.  **Detection**: Detects if a face exists in the uploaded image (using `retinaface`).
    2.  **Embedding**: Converts the face into a 128/512-dimensional vector (ArcFace).
    3.  **Matching**: Calculates **Cosine Similarity** between the new face and all existing faces in the database.
    4.  **Thresholding**:
        -   **Strict Match**: Confidence > 85% → Auto-verified (Found).
        -   **Potential Match**: Confidence within tolerance → Flagged for Admin review.
- **Optimization**: Uses incremental matching (One-vs-All) to avoid re-calculating all pairs on every new submission.

#### D. Database (SQLite + SQLModel)
- **Location**: `backend/sqlite_database.db`
- **ORM**: SQLModel (wraps SQLAlchemy and Pydantic).
- **Models** (`backend/pages/helper/data_models.py`):
    -   `RegisteredCases`: Stores "Missing" (Admin-submitted) data. Includes `face_mesh` (stored as JSON string).
    -   `PublicSubmissions`: Stores "Sightings" (Public-submitted) data.
- **Status Codes**:
    -   `NF`: Not Found (Active).
    -   `F`: Found (Resolved).

---

## 2. Feature-wise Breakdown

### A. Missing Person Registration (Admin)
- **Implementation**: A multi-step form (`RegisterCase.tsx`) capturing photo, personal details, reporter info, and FIR details.
- **Why**: Standardizes data intake. High-quality photos are crucial for AI accuracy.
- **Problem Solved**: Replaces unstructured paper/manual filing systems with a digital, searchable specific database.

### B. Public Sightings & Sighting Submission
- **Implementation**: A "Mobile App" view (`MobileApp.tsx`) allowing citizens to upload a photo/location of a suspected missing person.
- **Why**: Crowdsourcing is the most effective way to find people in large populations.
- **Problem Solved**: Bridges the gap between the public (who see the person) and the authorities (who have the missing report).

### C. AI-Based Face Matching
- **Implementation**: Automated background task triggered on every new case or sighting submission.
- **Why**: Manual matching is impossible at scale.
- **Problem Solved**: Instantly compares a new child against thousands of past missing reports, identifying matches that humans might miss due to aging or appearance changes.

### D. Case Status Handling (Missing / Found)
- **Implementation**: Explicit status flags (`NF`/`F`) in the database.
    -   **Missing (NF)**: Visible to public. Used for AI matching.
    -   **Found (F)**: Hidden from public browsing to protect privacy. Removed from matching pool.
- **Problem Solved**: Prevents "False Hope" by ensuring found children are not still advertised as missing.

---

## 3. Evolution of the System (Design Decisions)

### A. Removal of Streamlit Admin Flow
- **Previous**: The entire app was built in Streamlit (`backend/Home.py`).
- **Change**: Migrated to **React (Frontend) + FastAPI (Backend)**.
- **Technical Justification**: Streamlit is single-threaded and re-runs the entire script on interaction, leading to poor performance and "laggy" UI. React provides a fluid, state-driven client-side experience.
- **Usability Justification**: Custom styling, responsive mobile layouts, and complex multi-step forms are unmatched in React compared to Streamlit.

### B. Manual Match Confirmation Limitations
- **Previous**: Admins had to manually check every potential match.
- **Change**: Added **Auto-verification** for high-confidence matches (>85%).
- **Justification**: Reduces workload on police officers. If the AI is extremely sure, immediate alerts can be generated.

### C. Found Cases Visibility
- **Previous**: Found cases were sometimes still viewable or searchable.
- **Change**: **Strict filtering**. `NF` (Not Found) is the default query parameter. Found cases are explicitly excluded from public "Browse" views and AI candidate lists.
- **Ethical Justification**: Once a person is found, their right to privacy (Right to be Forgotten) overrides the public interest. Keeping them on a "Missing" poster is a safety risk and a privacy violation.

---

## 4. Current System Working (End-to-End Flow)

### Scenario: A Child Goes Missing

1.  **Registration**:
    -   Parent provides photo/details to Police/NGO.
    -   Admin logs into **Dashboard**, goes to **Register Case**.
    -   **Backend**: `POST /api/v1/cases` -> Saves image -> Extracts Face Embedding -> Saves to DB (`RegisteredCases`).
    -   **AI**: Background task runs `match_one_against_all` to see if this child was *already* sighted by someone completely different previously.

2.  **Sighting (The Match)**:
    -   A citizen sees a child alone at a railway station.
    -   Opens **Mobile Web App** -> **Submit Sighting**.
    -   Uploads photo and location.
    -   **Backend**: `POST /api/v1/public` -> Saves image -> Extracts Embedding -> Saves to DB (`PublicSubmissions`).

3.  **The Matching Algorithm**:
    -   Triggered immediately after Sighting submission.
    -   Calculates Cosine Distance between Sighting Embedding and ALL Missing Cases.
    -   **Result**: Distance `0.35` (High similarity).

4.  **Notification & Resolution**:
    -   **Admin Dashboard** -> **Match Cases** tab lights up.
    -   Admin sees "Potential Match: 85% Confidence".
    -   Admin compares photos side-by-side.
    -   Admin clicks **"Confirm Match"**.
    -   **System**: Updates both records to `status='F'` (Found). Links them in DB.
    -   **UI**: Child disappears from "Browse Missing" on Mobile App.

---

## 5. AI Design Justification

### Why ArcFace?
-   **Robustness**: ArcFace (ResNet50 based) is trained on massive datasets (MS-Celeb-1M). It maps faces to a geometric hypersphere where distances directly correspond to face similarity.
-   **Performance**: Superior to older methods like Eigenfaces or basic dlib HOG, especially with varying lighting or angles common in public sightings.

### The "Similarity Score"
-   We use **Cosine Distance** ($d$).
-   $Confidence = (1 - d) \times 100$.
-   **Thresholds**:
    -   Distance < 0.4 (Confidence > 60%): Potential Match.
    -   Distance < 0.2 (Confidence > 80%): Strong Match.
-   **Decision Support**: AI is treated as a **Filter**, not a Judge. It reduces 10,000 possibilities to 5, but the human officer makes the final call (Human-in-the-Loop).

### Minimizing False Positives
-   **Threshold Tuning**: We set a strict default tolerance ($0.60$) in `DeepFace` to avoid flagging random lookalikes.
-   **Context Data**: The UI displays text data (Age, Location) alongside the AI match, allowing the human to rule out obvious errors (e.g., matching a 5-year-old with a 20-year-old).

---

## 6. Ethical, Privacy & Safety Considerations

1.  **Right to Privacy (The "Found" Protocol)**
    -   **Mechanism**: The `status='NF'` filter is hardcoded in public endpoints.
    -   **Reasoning**: A recovered minor is a vulnerable individual. Their digital footprint as a "missing person" must be erased immediately upon recovery to prevent stigmatization or future harassment.

2.  **Anonymous Reporting**
    -   **Mechanism**: Mobile app does not require login for looking/reporting, only for tracking.
    -   **Reasoning**: Lowers the barrier to entry. People are more likely to help if they don't fear legal entanglement or tedious sign-up processes.

3.  **Data Minimization**
    -   **Mechanism**: We store Face Embeddings (numerical vectors), not just raw images.
    -   **Reasoning**: Even if the database is leaked, reconstructing the exact original face from a 512-d vector is mathematically difficult, adding a layer of security.

4.  **Panic Prevention**
    -   **Mechanism**: "Potential Matches" are visible ONLY to Admins, not to the public user who submitted the sighting.
    -   **Reasoning**: Telling a public user "You found him!" prematurely can lead to dangerous interventions or false hope for families. Only verified matches are communicated.

---

## 7. Limitations & Future Scope

### Limitations
1.  **Image Quality**: AI fails if the uploaded photo is blurry, too dark, or the face is occluded. 
2.  **Dataset Aging**: A child missing for 5 years will look different. Current ArcFace models are robust but not perfect at "Age Invariant" recognition without specialized fine-tuning.
3.  **Scalability**: Currently calculating One-vs-All matches ($O(N)$) in Python. For a nationwide system (millions of records), this requires a Vector Database (e.g., Milvus, Pinecone) for $O(\log N)$ retrieval.

### Future Scope
1.  **Video Analysis**: Integrating CCTV feed processing to auto-detect faces in crowds.
2.  **Geo-Fencing**: Prioritizing matches based on proximity (e.g., "Missing in Delhi" match "Sighted in Delhi" with higher weight).
3.  **Nationwide Sync**: API integration with CCTNS (India's Crime and Criminal Tracking Network & Systems).

---

## 8. Research Paper Readiness

This system is structured to support a research paper on **"AI-Assisted Humanitarian Recovery Systems"**.

-   **System Architecture Section**: Use Section 1 & 4 (React/FastAPI/DeepFace flow).
-   **Methodology**: Use Section 5 (ArcFace, Cosine Similarity, Decision Support thresholds).
-   **Design Decisions**: Use Section 3 (Evolution from Streamlit).
-   **Ethical Considerations**: Use Section 6 (Privacy, Data Handling).

---
*Generated by Reunite AI System Analyst Agent - January 2026*
