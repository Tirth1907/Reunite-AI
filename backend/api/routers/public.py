"""
Public Submissions router - CRUD operations for public sightings
"""

import os
import uuid
import json
from datetime import datetime
from typing import List, Optional
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
import numpy as np
import PIL.Image

from pages.helper import db_queries
from pages.helper.data_models import PublicSubmissions

router = APIRouter()


class PublicSubmissionResponse(BaseModel):
    id: str
    status: str
    location: Optional[str] = None
    mobile: Optional[str] = None
    birth_marks: Optional[str] = None
    submitted_on: Optional[datetime] = None
    submitted_by: Optional[str] = None

    class Config:
        from_attributes = True


def extract_face_encoding_from_image(image_bytes: bytes) -> Optional[list]:
    """Extract face encoding from image bytes."""
    try:
        from deepface import DeepFace
        from io import BytesIO
        
        image = PIL.Image.open(BytesIO(image_bytes)).convert("RGB")
        image_array = np.array(image)
        
        # Enforce detection to ensure a face exists
        embedding_objs = DeepFace.represent(
            img_path=image_array,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=True,
            align=True
        )
        
        if embedding_objs:
            # Return the embedding of the first face found
            return embedding_objs[0]["embedding"]
        return None
    except ImportError:
        return None
    except Exception as e:
        print(f"Error extracting face encoding: {e}")
        return None


@router.get("", response_model=List[PublicSubmissionResponse])
async def list_public_submissions(status: Optional[str] = "NF"):
    """List public submissions/sightings. use status='All' for everything."""
    try:
        cases = db_queries.fetch_public_cases(train_data=False, status=status)
        
        result = []
        for case in cases:
            result.append(PublicSubmissionResponse(
                id=case[0],
                status=case[1],
                location=case[2],
                mobile=case[3],
                birth_marks=case[4],
                submitted_on=case[5] if len(case) > 5 else None,
                submitted_by=case[6] if len(case) > 6 else None,
            ))
        
        return result
    except Exception as e:
        print(f"Error fetching public submissions: {e}")
        return []


@router.post("", response_model=PublicSubmissionResponse)
async def submit_sighting(
    location: str = Form(...),
    mobile: str = Form(...),
    birth_marks: str = Form(""),
    email: str = Form(""),
    submitted_by: str = Form("Anonymous"),
    photo: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Submit a public sighting of a potentially missing person.
    """
    # Read and save photo
    photo_bytes = await photo.read()
    submission_id = str(uuid.uuid4())
    photo_filename = f"{submission_id}.jpg"
    photo_path = os.path.join("resources", photo_filename)
    
    os.makedirs("resources", exist_ok=True)
    with open(photo_path, "wb") as f:
        f.write(photo_bytes)
    
    # Extract face encoding in thread pool
    face_encoding = await run_in_threadpool(extract_face_encoding_from_image, photo_bytes)
    
    if not face_encoding:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        raise HTTPException(
            status_code=400, 
            detail="No face detected in the image. Please upload a clear photo of the person's face."
        )
    
    # Create submission record
    submission = PublicSubmissions(
        id=submission_id,
        submitted_by=submitted_by,
        face_mesh=json.dumps(face_encoding),
        location=location,
        mobile=mobile,
        email=email,
        status="NF",  # Not Found / Under Review
        birth_marks=birth_marks,
    )
    
    db_queries.new_public_case(submission)
    
    # Trigger background matching
    if background_tasks:
        from pages.helper import match_algo
        background_tasks.add_task(
            match_algo.match_one_against_all, 
            case_id=submission_id, 
            case_type="public"
        )
    
    return PublicSubmissionResponse(
        id=submission_id,
        status="NF",
        location=location,
        mobile=mobile,
        birth_marks=birth_marks,
    )


@router.get("/{submission_id}")
async def get_submission(submission_id: str):
    """Get details of a specific public submission."""
    try:
        result = db_queries.get_public_submission_basic(submission_id)
        if not result:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        return {
            "id": result[0],
            "status": result[1],
            "location": result[2],
            "birth_marks": result[3],
            "submitted_on": result[4],
            "photo_url": f"/resources/{submission_id}.jpg",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{submission_id}")
async def delete_submission(submission_id: str):
    """Delete a public submission."""
    try:
        db_queries.delete_public_case(submission_id)
        
        # Also delete photo if exists
        photo_path = os.path.join("resources", f"{submission_id}.jpg")
        if os.path.exists(photo_path):
            os.remove(photo_path)
        
        return {"status": "deleted", "id": submission_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{submission_id}/status")
async def get_submission_status(submission_id: str):
    """Get status of a public submission."""
    try:
        result = db_queries.get_public_submission_basic(submission_id)
        if not result:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        return {
            "id": result[0], 
            "status": result[1]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
