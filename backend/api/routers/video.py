"""
Reunite AI Phase 2 — Video Analysis API Router

Endpoints:
  POST /api/v2/video/upload           Upload CCTV video + select case
  GET  /api/v2/video/status/{video_id} Poll processing progress
  GET  /api/v2/video/results/{case_id} Fetch detection results for a case
"""

import os
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel

from pages.helper import db_queries
from pages.helper.data_models import VideoUploads
from pages.helper.video_processor import (
    VIDEO_UPLOADS_DIR,
    ALLOWED_EXTENSIONS,
    validate_video_file,
    process_video,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class VideoUploadResponse(BaseModel):
    video_id: str
    case_id: str
    status: str
    message: str


class VideoStatusResponse(BaseModel):
    video_id: str
    status: str
    total_frames: Optional[int] = None
    processed_frames: int = 0
    total_detections: int = 0
    progress_percent: float = 0.0
    error_message: Optional[str] = None


class DetectionItem(BaseModel):
    id: str
    video_id: str
    video_location: Optional[str] = None
    timestamp_seconds: float
    timestamp_display: str
    confidence: float
    cropped_face_url: str
    detected_at: Optional[datetime] = None


class VideoResultsResponse(BaseModel):
    case_id: str
    case_name: Optional[str] = None
    total_videos_analyzed: int = 0
    detections: List[DetectionItem] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS display string."""
    total = int(seconds)
    hrs = total // 3600
    mins = (total % 3600) // 60
    secs = total % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=VideoUploadResponse, status_code=201)
async def upload_video(
    video: UploadFile = File(...),
    case_id: str = Form(...),
    video_location: str = Form(""),
    confidence_threshold: float = Form(0.60),
    background_tasks: BackgroundTasks = None,
):
    """
    Upload a CCTV video file for analysis against a specific missing case.

    - **video**: Video file (.mp4, .avi, .mkv, .mov, .wmv) — max 2 GB
    - **case_id**: ID of the registered missing case to match against
    - **video_location**: Optional CCTV camera location description
    - **confidence_threshold**: Match threshold (0.0–1.0). Default 0.60
    """
    # Validate case exists
    case_detail = db_queries.get_registered_case_detail(case_id)
    if not case_detail:
        raise HTTPException(status_code=404, detail="Selected case not found in database.")

    # Validate file extension
    ext = os.path.splitext(video.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Save video file to disk
    video_id = str(uuid.uuid4())
    safe_filename = f"{video_id}{ext}"
    file_path = os.path.join(VIDEO_UPLOADS_DIR, safe_filename)

    os.makedirs(VIDEO_UPLOADS_DIR, exist_ok=True)

    try:
        contents = await video.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    # Validate video after saving
    ok, error = validate_video_file(file_path)
    if not ok:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=error)

    # Create database record
    upload_record = VideoUploads(
        id=video_id,
        filename=video.filename or safe_filename,
        file_path=file_path,
        case_id=case_id,
        status="queued",
        video_location=video_location or None,
        confidence_threshold=confidence_threshold,
    )
    db_queries.create_video_upload(upload_record)

    # Start background processing
    if background_tasks:
        background_tasks.add_task(process_video, video_id)

    return VideoUploadResponse(
        video_id=video_id,
        case_id=case_id,
        status="queued",
        message="Video uploaded successfully. Processing will begin shortly.",
    )


@router.get("/status/{video_id}", response_model=VideoStatusResponse)
async def get_video_status(video_id: str):
    """
    Poll the processing status of an uploaded video.

    Returns current progress (frames processed / total) and detection count.
    """
    upload = db_queries.get_video_upload(video_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Video upload not found.")

    progress = 0.0
    if upload.total_frames and upload.total_frames > 0:
        progress = round((upload.processed_frames / upload.total_frames) * 100, 1)

    return VideoStatusResponse(
        video_id=upload.id,
        status=upload.status,
        total_frames=upload.total_frames,
        processed_frames=upload.processed_frames,
        total_detections=upload.total_detections,
        progress_percent=progress,
        error_message=upload.error_message,
    )


@router.get("/results/{case_id}", response_model=VideoResultsResponse)
async def get_video_results(case_id: str):
    """
    Fetch all video detection results for a specific missing case.

    Returns matched timestamps, confidence scores, cropped face URLs,
    and the CCTV location for each detection.
    """
    # Get case name
    case_detail = db_queries.get_registered_case_detail(case_id)
    case_name = None
    if case_detail and len(case_detail) > 0:
        case_name = case_detail[0][0] if isinstance(case_detail[0], tuple) else None

    # Get all video uploads for this case
    uploads = db_queries.get_video_uploads_by_case(case_id)
    upload_map = {u.id: u for u in uploads} if uploads else {}

    # Get all detections for this case
    detections = db_queries.get_video_detections_by_case(case_id)

    detection_items = []
    for det in (detections or []):
        vid_upload = upload_map.get(det.video_id)
        video_location = vid_upload.video_location if vid_upload else None

        detection_items.append(DetectionItem(
            id=det.id,
            video_id=det.video_id,
            video_location=video_location,
            timestamp_seconds=det.timestamp_seconds,
            timestamp_display=_format_timestamp(det.timestamp_seconds),
            confidence=det.confidence,
            cropped_face_url=f"/resources/{det.cropped_face_path}",
            detected_at=det.detected_at,
        ))

    return VideoResultsResponse(
        case_id=case_id,
        case_name=case_name,
        total_videos_analyzed=len(upload_map),
        detections=detection_items,
    )
