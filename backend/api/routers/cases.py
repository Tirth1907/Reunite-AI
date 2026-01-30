"""
Registered Cases router - CRUD operations for missing person cases
"""

import os
import uuid
import json
from datetime import datetime
from io import BytesIO
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
import numpy as np
import PIL.Image

from pages.helper import db_queries
from pages.helper.data_models import RegisteredCases

router = APIRouter()


class CaseResponse(BaseModel):
    id: str
    name: str
    age: str
    status: str
    last_seen: str
    birth_marks: Optional[str] = None
    matched_with: Optional[str] = None
    complainant_mobile: Optional[str] = None
    submitted_on: Optional[datetime] = None
    photo_url: Optional[str] = None
    father_name: Optional[str] = None
    address: Optional[str] = None
    complainant_name: Optional[str] = None

    class Config:
        from_attributes = True


def extract_face_encoding_from_image(image_bytes: bytes) -> Optional[list]:
    """Extract face encoding from image bytes using DeepFace."""
    try:
        from deepface import DeepFace
        
        image = PIL.Image.open(BytesIO(image_bytes)).convert("RGB")
        image_array = np.array(image)
        
        embedding_objs = DeepFace.represent(
            img_path=image_array,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=True,
            align=True
        )
        
        if embedding_objs:
            return embedding_objs[0]["embedding"]
        
        print("No face detected in image (DeepFace)")
        return None
        
    except ImportError:
        print("DeepFace not installed or model missing")
        return None
    except Exception as e:
        print(f"Error extracting face encoding: {e}")
        return None


@router.get("", response_model=List[CaseResponse])
async def list_cases(
    status: Optional[str] = "All",
    submitted_by: Optional[str] = None,
    limit: Optional[int] = None,
):
    """List registered cases."""
    try:
        if submitted_by:
            cases = db_queries.fetch_registered_cases(submitted_by, status)
        else:
            if status == "Not Found" or status == "NF":
                cases = db_queries.fetch_all_not_found_registered_cases()
            else:
                # For "All", "Found", or any other status - fetch all cases
                cases = db_queries.fetch_all_registered_cases()

        result = []
        for case in cases:
            def get_idx(tup, idx):
                return tup[idx] if isinstance(tup, tuple) and len(tup) > idx else None

            case_id = case[0] if isinstance(case, tuple) else case.id
            name = case[1] if isinstance(case, tuple) else case.name
            age = str(case[2]) if isinstance(case, tuple) else str(case.age)
            status_val = case[3] if isinstance(case, tuple) else case.status
            last_seen = case[4] if isinstance(case, tuple) else case.last_seen

            birth_marks = None
            matched_with = None
            father_name = None
            address = None
            comp_name = None
            comp_mobile = None
            sub_on = None

            if isinstance(case, tuple):
                if submitted_by: 
                    matched_with = get_idx(case, 5)
                    comp_mobile = get_idx(case, 6)
                    birth_marks = get_idx(case, 7)
                    father_name = get_idx(case, 8)
                    address = get_idx(case, 9)
                    comp_name = get_idx(case, 10)
                    sub_on = get_idx(case, 11)
                else:
                    birth_marks = get_idx(case, 5)
                    father_name = get_idx(case, 6)
                    address = get_idx(case, 7)
                    comp_name = get_idx(case, 8)
                    comp_mobile = get_idx(case, 9)
                    sub_on = get_idx(case, 10)
            else:
                birth_marks = getattr(case, 'birth_marks', None)
                matched_with = getattr(case, 'matched_with', None)
                father_name = getattr(case, 'father_name', None)
                address = getattr(case, 'address', None)
                comp_name = getattr(case, 'complainant_name', None)

            result.append(CaseResponse(
                id=case_id,
                name=name,
                age=age,
                status=status_val,
                last_seen=last_seen,
                birth_marks=birth_marks,
                matched_with=matched_with,
                complainant_mobile=comp_mobile,
                father_name=father_name,
                address=address,
                complainant_name=comp_name,
                submitted_on=sub_on,
                photo_url=f"/resources/{case_id}.jpg",
            ))
        
        if limit:
            result = result[:limit]
        
        return result
    except Exception as e:
        print(f"Error fetching cases: {e}")
        return []


@router.post("", response_model=CaseResponse)
async def register_case(
    name: str = Form(...),
    age: str = Form(...),
    father_name: str = Form(""),
    last_seen: str = Form(...),
    address: str = Form(""),
    complainant_name: str = Form(""),
    complainant_mobile: str = Form(""),
    adhaar_card: str = Form(""),
    birth_marks: str = Form(""),
    submitted_by: str = Form("Admin"),
    photo: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Register a new missing person case with photo."""
    # Read and save photo
    photo_bytes = await photo.read()
    case_id = str(uuid.uuid4())
    photo_filename = f"{case_id}.jpg"
    photo_path = os.path.join("resources", photo_filename)
    
    os.makedirs("resources", exist_ok=True)
    with open(photo_path, "wb") as f:
        f.write(photo_bytes)
    
    # Extract face encoding in thread pool to avoid blocking
    face_encoding = await run_in_threadpool(extract_face_encoding_from_image, photo_bytes)
    
    if not face_encoding:
        # cleanup saved photo
        if os.path.exists(photo_path):
            os.remove(photo_path)
        raise HTTPException(
            status_code=400, 
            detail="No face detected in the image. Please upload a clear photo of the person's face."
        )
    
    # Create case record
    case = RegisteredCases(
        id=case_id,
        submitted_by=submitted_by,
        name=name,
        father_name=father_name,
        age=age,
        complainant_name=complainant_name,
        complainant_mobile=complainant_mobile,
        adhaar_card=adhaar_card,
        last_seen=last_seen,
        address=address,
        face_mesh=json.dumps(face_encoding),
        status="NF",
        birth_marks=birth_marks,
    )
    
    db_queries.register_new_case(case)
    
    # Trigger background matching
    if background_tasks:
        from pages.helper import match_algo
        background_tasks.add_task(
            match_algo.match_one_against_all, 
            case_id=case_id, 
            case_type="registered"
        )
    
    return CaseResponse(
        id=case_id,
        name=name,
        age=age,
        status="NF",
        last_seen=last_seen,
        birth_marks=birth_marks,
        photo_url=f"/resources/{case_id}.jpg",
    )


@router.get("/{case_id}")
async def get_case(case_id: str):
    """Get details of a specific registered case."""
    try:
        result = db_queries.get_registered_case_detail(case_id)
        if not result:
            raise HTTPException(status_code=404, detail="Case not found")
        
        case = result[0]
        return {
            "id": case_id,
            "name": case[0],
            "complainant_mobile": case[1],
            "age": case[2],
            "last_seen": case[3],
            "birth_marks": case[4],
            "father_name": case[5] if len(case) > 5 else None,
            "address": case[6] if len(case) > 6 else None,
            "complainant_name": case[7] if len(case) > 7 else None,
            "submitted_on": case[8] if len(case) > 8 else None,
            "status": case[9] if len(case) > 9 else None,
            "submitted_by": case[10] if len(case) > 10 else None,
            "photo_url": f"/resources/{case_id}.jpg",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{case_id}")
async def delete_case(case_id: str):
    """Delete a registered case."""
    try:
        db_queries.delete_registered_case(case_id)
        
        photo_path = os.path.join("resources", f"{case_id}.jpg")
        if os.path.exists(photo_path):
            os.remove(photo_path)
        
        return {"status": "deleted", "id": case_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
