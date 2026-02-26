# Reunite AI v1.5 — Phase 2

> AI-powered missing persons recovery system for Indian police stations

## Features

### Phase 1 (v1.5)
- **Missing Person Registration** — Admin dashboard with photo upload and case details
- **Public Sightings** — Mobile-friendly anonymous reporting
- **AI Face Matching** — ArcFace + RetinaFace automatic face comparison
- **Case Management** — Status tracking (Missing/Found), admin review
- **Auto-verification** — High-confidence matches (>85%) auto-verified

### Phase 2 (NEW)
- **CCTV Video Analysis** — Upload recorded CCTV footage for AI scanning
- **Single-case Matching** — Select one missing person to search for
- **Frame Extraction** — Extracts frames every 2 seconds at 640×480
- **Detection Results** — Timestamps, cropped faces, confidence scores
- **GPU Acceleration** — GTX 1650 (4GB VRAM) with CPU fallback
- **92% Workload Reduction** — Officers review only AI-flagged timestamps

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI, Python 3.10+ |
| Database | SQLite + SQLModel |
| AI | DeepFace (ArcFace + RetinaFace) |
| Video | OpenCV (Phase 2) |

## Quick Start

```powershell
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173

## Documentation

- [Phase 2 Architecture](backend/docs/Phase2_Architecture.md)
- [Windows Setup Guide](backend/docs/WINDOWS_SETUP.md)
- [System Analysis](SYSTEM_ANALYSIS.md)

## API Endpoints

### Phase 1
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/auth/login | Admin login |
| POST | /api/v1/cases | Register missing case |
| GET | /api/v1/cases | List all cases |
| POST | /api/v1/public | Submit sighting |
| POST | /api/v1/matching/run | Run AI matching |

### Phase 2
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v2/video/upload | Upload CCTV video |
| GET | /api/v2/video/status/{id} | Poll processing progress |
| GET | /api/v2/video/results/{id} | Get detection results |

## Hardware Requirements

- Intel i5 12th Gen (or equivalent)
- NVIDIA GTX 1650 (4GB VRAM) — optional, CPU fallback available
- 16 GB RAM
- Windows 10/11
