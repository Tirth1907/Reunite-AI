# Reunite AI — Phase 2 Architecture Document
# Offline CCTV Batch Analysis System

## Overview

Phase 2 extends Reunite AI v1.5 with an **Offline CCTV Batch Analysis System** that automates the scanning of recorded CCTV footage for missing persons. This eliminates 80-90% of manual video-watching workload for police officers.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   FRONTEND (React + TypeScript)                 │
│                                                                  │
│  VideoAnalysis.tsx                                                │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │  Case     │  │  Video       │  │  Results Timeline         │  │
│  │  Selector │  │  Upload      │  │  (Cropped faces,          │  │
│  │  Dropdown │  │  Drag+Drop   │  │   timestamps,             │  │
│  │           │  │              │  │   confidence %)            │  │
│  └──────────┘  └──────────────┘  └───────────────────────────┘  │
│                                                                  │
│  API Layer (api.ts) ── uploadVideo / getVideoStatus / getResults │
└──────────────────────────────┬──────────────────────────────────┘
                                │  HTTP REST
┌──────────────────────────────▼──────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│                                                                  │
│  /api/v2/video/upload        POST   Upload video + select case  │
│  /api/v2/video/status/{id}   GET    Poll processing progress    │
│  /api/v2/video/results/{id}  GET    Fetch detection results     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               video_processor.py (BackgroundTasks)         │ │
│  │                                                            │ │
│  │  1. Load case embedding from DB                            │ │
│  │  2. Open video with OpenCV                                 │ │
│  │  3. Extract frame every 2 seconds                          │ │
│  │  4. Resize to 640x480                                      │ │
│  │  5. Detect faces (RetinaFace)                              │ │
│  │  6. Generate embeddings (ArcFace)                          │ │
│  │  7. Compare with cosine distance                           │ │
│  │  8. Save detections if confidence > threshold              │ │
│  │  9. Update progress every 10 frames                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────┐                       │
│  │         SQLite Database              │                       │
│  │  ┌─────────────────┐                │                       │
│  │  │  VideoUploads    │ (status,       │                       │
│  │  │                  │  progress,     │                       │
│  │  │                  │  case_id)      │                       │
│  │  └─────────────────┘                │                       │
│  │  ┌─────────────────┐                │                       │
│  │  │ VideoDetections  │ (timestamp,    │                       │
│  │  │                  │  confidence,   │                       │
│  │  │                  │  cropped_face) │                       │
│  │  └─────────────────┘                │                       │
│  └──────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### VideoUploads
| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique video upload ID |
| filename | str | Original filename |
| file_path | str | Server storage path |
| case_id | str (FK) | Selected missing case |
| status | str | queued → processing → done / failed |
| total_frames | int | Total frames to process |
| processed_frames | int | Frames processed so far |
| total_detections | int | Matched faces count |
| error_message | str | Error details if failed |
| video_location | str | CCTV camera location |
| confidence_threshold | float | Match threshold |
| uploaded_at | datetime | Upload timestamp |
| completed_at | datetime | Processing completion |

### VideoDetections
| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique detection ID |
| video_id | str (FK) | Parent video |
| case_id | str (FK) | Matched case |
| timestamp_seconds | float | Position in video |
| confidence | float | Match confidence (%) |
| cropped_face_path | str | Saved face image path |
| frame_number | int | Frame index |
| detected_at | datetime | Detection timestamp |

## AI Pipeline Details

### Face Detection: RetinaFace
- Multi-scale face detector with landmark localization
- Handles varying face sizes, angles, and partial occlusion
- Produces bounding boxes for face cropping

### Face Embedding: ArcFace (ResNet50)
- Generates 512-dimensional face embeddings
- Trained on MS-Celeb-1M dataset
- Maps faces to a hypersphere where distance = dissimilarity

### Matching: Cosine Similarity
```
Confidence = (1 - cosine_distance) × 100%
```
- **≥ 85%**: High confidence — strong match
- **60-84%**: Potential match — requires review
- **< 60%**: Below threshold — not flagged

## GPU/CPU Fallback
1. TensorFlow auto-detects CUDA GPUs
2. If GTX 1650 available: VRAM limited to 2GB, processing ~15 min for 15-min video
3. If no GPU: CPU fallback transparent, processing ~45 min for 15-min video
4. No code changes needed — fallback is automatic

## Memory Management
- One frame in memory at a time (640×480 × 3 bytes = ~900 KB)
- Batch DB writes every 10 frames
- Video not loaded into memory (streamed by OpenCV)
- VRAM capped at 2GB via TensorFlow config
- Peak RAM < 4GB even for 15-minute videos

## Workload Reduction Analysis

### Before (Manual Process)
- Officer watches 15 min of footage = 15 min
- 10 cameras × 15 min = **150 minutes** of watching
- Human fatigue reduces accuracy after 30 min

### After (AI-Assisted)
- Upload 10 videos = 2 min
- AI processes all (background) = 0 min officer time
- Review flagged detections = 5-10 min
- **Total: ~12 min = 92% reduction**

## Files Added/Modified

### New Files
| File | Purpose |
|---|---|
| `backend/pages/helper/video_processor.py` | Core video processing pipeline |
| `backend/api/routers/video.py` | Video analysis API endpoints |
| `frontend/src/app/pages/dashboard/VideoAnalysis.tsx` | UI for upload, processing, results |
| `backend/docs/Phase2_Architecture.md` | This document |
| `backend/docs/WINDOWS_SETUP.md` | Windows setup guide |

### Modified Files
| File | Change |
|---|---|
| `backend/pages/helper/data_models.py` | Added VideoUploads, VideoDetections models |
| `backend/pages/helper/db_queries.py` | Added 7 video query functions, updated create_db() |
| `backend/main.py` | Registered /api/v2/video router, mounted static dirs |
| `backend/requirements.txt` | Added opencv-python==4.9.0.80 |
| `frontend/src/app/services/api.ts` | Added video API functions |
| `frontend/src/app/App.tsx` | Added video-analysis route |
| `frontend/src/app/components/DashboardLayout.tsx` | Added CCTV Analysis nav item |
