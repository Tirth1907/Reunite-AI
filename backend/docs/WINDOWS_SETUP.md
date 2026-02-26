# Reunite AI Phase 2 — Windows Setup Guide

## Prerequisites

| Software | Version | Download |
|---|---|---|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| Git | Latest | [git-scm.com](https://git-scm.com/) |
| NVIDIA Drivers | Latest | [nvidia.com/drivers](https://www.nvidia.com/drivers) (for GPU) |

## Step 1: Clone & Setup Python Environment

```powershell
cd "C:\Users\YourName\Desktop"
git clone https://github.com/Tirth1907/Reunite-AI.git "Reunite AI 1.5"
cd "Reunite AI 1.5"

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt
```

### GPU Acceleration (Optional but Recommended)

If you have an NVIDIA GPU (GTX 1650 or better):

```powershell
# Install CUDA-enabled TensorFlow (requires CUDA 11.2+ and cuDNN 8.1+)
pip install tensorflow[and-cuda]
```

To verify GPU is detected:
```powershell
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

If no GPU output, the system will automatically fall back to CPU.

## Step 2: Setup Frontend

```powershell
cd frontend
npm install
cd ..
```

## Step 3: Run the Application

### Terminal 1: Backend
```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

### Terminal 2: Frontend
```powershell
cd frontend
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Step 4: Using CCTV Analysis (Phase 2)

1. Log in to the dashboard
2. Click **"CCTV Analysis"** in the sidebar
3. Select a missing person case from the dropdown
4. Upload a CCTV video file (MP4, AVI, MKV — max 2 GB)
5. Optionally enter the CCTV camera location
6. Click **"Start AI Analysis"**
7. Wait for processing to complete (progress bar shows status)
8. Review detection results — each detection shows:
   - Cropped face image
   - Timestamp in the video
   - Confidence score
   - CCTV location

## Troubleshooting

### "No face detected" errors
- Ensure the case photo has a clear, unobstructed face
- Try a better quality photo for the missing person case

### Processing is slow
- Verify GPU is being used: check console output for "GPU detected"
- Processing time: ~1 min per minute of video (GPU) or ~3 min per minute (CPU)
- 15-minute video: ~15 min (GPU) / ~45 min (CPU)

### Out of memory
- Close other GPU-intensive applications
- The system limits VRAM to 2 GB, but other apps may compete
- For CPU fallback: set environment variable `CUDA_VISIBLE_DEVICES=-1`

### SQLite database locked
- Ensure only one instance of the backend is running
- Stop and restart the backend server

## Directory Structure (Phase 2 Additions)

```
backend/
├── video_uploads/              Auto-created, stores uploaded videos
├── resources/
│   └── video_detections/       Auto-created, stores cropped face images
├── pages/helper/
│   └── video_processor.py      Core processing engine
├── api/routers/
│   └── video.py                Video analysis API
└── docs/
    ├── Phase2_Architecture.md  Architecture document
    └── WINDOWS_SETUP.md        This guide
```
