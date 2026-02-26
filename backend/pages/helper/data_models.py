from uuid import uuid4
from datetime import datetime
from typing import Optional

from sqlmodel import Field, create_engine, SQLModel


class PublicSubmissions(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
   
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4()), nullable=False
    )
    submitted_by: str = Field(max_length=128, nullable=True)
    face_mesh: str = Field(nullable=False)  
    location: str = Field(max_length=128, nullable=True)
    mobile: str = Field(max_length=10, nullable=False)
    email: str = Field(max_length=64, nullable=True)
    status: str = Field(max_length=16, nullable=False)
    birth_marks: str = Field(max_length=512, nullable=True)
    
    submitted_on: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class RegisteredCases(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4()), nullable=False
    )
    submitted_by: str = Field(max_length=64, nullable=False)
    name: str = Field(max_length=128, nullable=False)
    father_name: str = Field(max_length=128, nullable=True)
    age: str = Field(max_length=8, nullable=True)
    complainant_name: str = Field(max_length=128)
    complainant_mobile: str = Field(max_length=10, nullable=True)
    adhaar_card: str = Field(max_length=12)
    last_seen: str = Field(max_length=64)
    address: str = Field(max_length=512)
    face_mesh: str = Field(nullable=False)  
    submitted_on: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    status: str = Field(max_length=16, nullable=False)
    birth_marks: str = Field(max_length=512)
    matched_with: str = Field(nullable=True)



class VideoUploads(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4()), nullable=False
    )
    filename: str = Field(max_length=256, nullable=False)
    file_path: str = Field(max_length=512, nullable=False)
    case_id: str = Field(max_length=64, nullable=False)
    status: str = Field(max_length=16, nullable=False, default="queued")
    total_frames: Optional[int] = Field(default=None, nullable=True)
    processed_frames: int = Field(default=0, nullable=False)
    total_detections: int = Field(default=0, nullable=False)
    error_message: Optional[str] = Field(default=None, max_length=512, nullable=True)
    video_location: Optional[str] = Field(default=None, max_length=256, nullable=True)
    confidence_threshold: float = Field(default=0.60, nullable=False)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)


class VideoDetections(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4()), nullable=False
    )
    video_id: str = Field(max_length=64, nullable=False)
    case_id: str = Field(max_length=64, nullable=False)
    timestamp_seconds: float = Field(nullable=False)
    confidence: float = Field(nullable=False)
    cropped_face_path: str = Field(max_length=512, nullable=False)
    frame_number: int = Field(nullable=False)
    detected_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


if __name__ == "__main__":
    sqlite_url = "sqlite:///example.db"
    engine = create_engine(sqlite_url)

    RegisteredCases.__table__.create(engine)
    PublicSubmissions.__table__.create(engine)
    VideoUploads.__table__.create(engine)
    VideoDetections.__table__.create(engine)
