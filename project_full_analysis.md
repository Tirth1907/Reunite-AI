# Reunite AI System Analysis Report

## 1. Project Overview
**Reunite AI** is an AI-powered platform designed to facilitate the search for missing persons through advanced face recognition and automated video analysis. The system allows users to register missing persons with reference photos and then analyzes various photo submissions or surveillance (CCTV) footage to find a match.

The project addresses the challenge of manually scanning hours of CCTV footage or large numbers of public sightings. It implements a sophisticated two-pass video processing pipeline to ensure both speed and accuracy.

### Overall System Workflow
1.  **Case Registration**: A missing person's case is registered with a high-quality "anchor" photo.
2.  **Embedding Extraction**: The anchor photo is processed (RetinaFace/MTCNN + ArcFace) to generate a unique 512-dimensional vector.
3.  **Submission/Upload**: Public sightings (photos) or surveillance videos are uploaded to the system.
4.  **AI Analysis**:
    *   **Photos**: Direct comparison between the submission embedding and registered cases.
    *   **Videos**: A two-pass analysis (Pass 1: Strict, Pass 2: Fallback) processes frames at intervals, detects faces, and compares them to the target case.
5.  **Result Generation**: Matched frames are cropped, saved, and presented with confidence scores and timestamps.

---

## 2. Complete System Architecture
The system follows a classic client-server architecture with specialized AI components.

*   **Frontend**: Built with **React** (Vite-based), implementing a modern, responsive UI for case management and sighting submission. It communicates with the backend via RESTful APIs.
*   **Backend**: A **FastAPI** (Python) server that handles orchestration, database operations, and triggers background processing tasks.
*   **APIs**:
    *   `v1/auth`: User authentication and role management.
    *   `v1/cases`: CRUD operations for registered missing persons.
    *   `v1/public`: Handling of public sighting submissions.
    *   `v1/matching`: Cross-referencing sightings with registered cases.
    *   `v2/video`: Asynchronous video processing and status tracking.
*   **AI Models**: Uses a suite of models including **RetinaFace** (Pass 1), **ArcFace** (Embeddings), **YOLOv8** (Pre-screener), and **Haar Cascades** (Fast pre-filter).
*   **Database**: **SQLite** managed via **SQLModel** (SQLAlchemy-based ORM), storing case metadata, user info, and detection logs.
*   **Communication**: Frontend (Axios/Fetch) -> Backend (FastAPI/Pydantic) -> AI Pipeline (BackgroundTasks/OpenCV/DeepFace).

---

## 3. Repository Folder Structure

### Root Directory
*   `backend/` → The Python backend application.
*   `frontend/` → The React frontend application.
*   `docs/` → Project documentation, analysis, and flowcharts.
*   `git_history_recent.txt` → Logs of recent changes for auditing.

### `backend/`
*   `main.py` → FastAPI entry point; configures CORS, mounts routers, and serves static resources.
*   `api/` → API logic.
    *   `routers/` → Route definitions (auth, cases, public, matching, video).
    *   `schemas/` → Pydantic models for request/response validation.
*   `pages/helper/` → Core logic and business rules.
    *   `video_processor.py` → **Main video analysis engine**.
    *   `fallback_detector.py` → Lightweight detection logic for Pass 2.
    *   `registration_encoder.py` → Face encoding logic for cases.
    *   `db_queries.py` → Database access layer.
    *   `match_algo.py` → Algorithms for matching sightings.
    *   `yolo_prescreener.py` → YOLOv8 optimization for Pass 1.
*   `resources/` → Storage for uploaded photos and detection results.
*   `video_uploads/` → Temporary storage for uploaded CCTV videos.
*   `requirements.txt` → Backend dependencies.

### `frontend/`
*   `src/app/` → Main application logic.
    *   `pages/` → UI Views (Landing, Auth, Dashboard).
    *   `services/api.ts` → Centralized API client for backend communication.
    *   `components/` → Reusable UI elements.
    *   `context/` → Global state management (e.g., AuthContext).

---

## 4. Video Processing Pipeline

The system uses a highly optimized pipeline to handle large video files on standard hardware.

```
Video Upload
↓
Validation (Format, Size, Duration)
↓
Background Queue (FastAPI BackgroundTasks)
↓
Pass 1: Strict CCTV Mode
  ├─ Adaptive Frame Sampling (e.g., every 3-15s based on length)
  ├─ Fast Pre-Filter (Haar Cascade - Tightened to reduce false positives)
  ├─ Face Detection (RetinaFace - Accurate but slow)
  └─ Identity Verification (ArcFace Embedding + Cosine Distance)
↓
No Matches Found? → Trigger Pass 2
↓
Pass 2: Fallback Pass
  ├─ Denser Frame Sampling (e.g., every 1-4s)
  ├─ Image Enhancement (CLAHE)
  ├─ Face Detection (OpenCV Haar - Very fast, works for angled/small faces)
  └─ Identity Verification (ArcFace Embedding + Relaxed Thresholds)
↓
Detection Saved to DB (with cropped face image)
```

**Key Files/Functions**:
*   `video.py`: Handles upload and queues `process_video`.
*   `video_processor.py`: Implements `_run_processing_pass`.
*   `fallback_detector.py`: Implements `detect_face_fallback` using the OpenCV backend.

---

## 5. AI Models and Algorithms Used

| Model | Purpose | Library | File Responsible |
|-------|---------|---------|------------------|
| **YOLOv8** | Fast face pre-screener (15ms/frame) to skip empty frames in Pass 1. | `ultralytics` | `yolo_prescreener.py` |
| **RetinaFace** | High-precision face detector (400ms/frame) used in Pass 1. | `DeepFace` | `video_processor.py` |
| **ArcFace** | Face recognition model generating 512-dim embeddings. | `DeepFace` | `registration_encoder.py` |
| **Haar Cascade** | Ultra-fast detector (3ms/frame) used for pre-filtering and Pass 2. | `OpenCV` | `video_processor.py` / `fallback_detector.py` |

**Why combined?**
The combination provides a "fail-early" system. Haar/YOLO filters out empty frames instantly, allowing the expensive RetinaFace to run ONLY when a face is likely present. ArcFace provides state-of-the-art recognition accuracy.

---

## 6. Frame Processing Logic
*   **Sequential Processing**: Frames are processed one-by-one to manage VRAM limits (limited to 2GB for GTX 1650 compatibility).
*   **Adaptive Sampling**: Sampling rate changes based on video duration to balance speed vs coverage (e.g., a 15-minute video might sample every 10-15s in Pass 1).
*   **Resizing**: Frames exceeding 1280x720 are downscaled to maintain performance without losing significant detail.
*   **Skipping**: Frames are skipped if they are empty (no faces) or if they are duplicates of the last saved detection (suppression window).

---

## 7. Detection and Matching Logic
*   **Cosine Distance**: The core metric for identity matching. 0.0 is identical; 2.0 is opposite.
*   **Strict Thresholds (Pass 1)**: Focus on high-quality matches. Distance <= 0.40 (~60% confidence).
*   **Relaxed Thresholds (Pass 2)**: Focus on finding sightings in poor light or angled shots. Distance <= 0.65 (~35% confidence).
*   **Suppression**: If multiple frames of the same person are detected sequentially, only the first frame in the window (default 3s) is saved to avoid spam.

---

## 8. Performance Characteristics
*   **Expensive Operations**: RetinaFace detection and ArcFace embedding generation are the primary bottlenecks.
*   **CPU vs GPU**: RetinaFace on CPU (~5000ms/frame) is extremely slow compared to GPU (~400ms/frame).
*   **Optimization**: Speed is achieved by skipping RetinaFace using YOLO/Haar pre-filters.
*   **Memory**: High RAM usage (~16GB recommended) due to DeepFace model loading and frame buffering.

---

## 9. Data Flow Diagram (Text-Based)

```text
USER (FRONTEND)
  └─ Upload Video + Select Case
       ↓
API (BACKEND)
  └─ Save Video → Disk (video_uploads/)
  └─ Create Record → DB (status="queued")
  └─ Start Worker → BackgroundTask(process_video)
       ↓
WORKER (video_processor.py)
  └─ Pass 1 (Strict/RetinaFace)
       ├─ Face Found? → Save Match → Result Available
       └─ Not Found? → Trigger Pass 2
            ↓
  └─ Pass 2 (Fallback/OpenCV)
       ├─ Face Found? (Relaxed) → Save Match → Result Available
       └─ Not Found? → Done (0 Matches)
```

---

## 10. Key Python Files Responsible for Processing

| File | Role |
|------|------|
| `main.py` | Server entry point & configuration. |
| `video_processor.py` | Orchestrates the two-pass video analysis pipeline. |
| `fallback_detector.py` | Provides fast, low-consequences detection for difficult frames. |
| `registration_encoder.py` | Ensures high-quality embeddings for case "anchor" photos. |
| `db_queries.py` | Manages persistence for cases, detections, and upload status. |
| `yolo_prescreener.py` | Adds YOLO-based optimization to accelerate overall processing. |
| `data_models.py` | Defines SQLModel classes for SQLite database. |
| `match_algo.py` | Implements logic for batch matching large groups of sightings. |
