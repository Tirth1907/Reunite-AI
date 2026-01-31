"""
Matching and Statistics router
"""

from typing import Optional
from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

from pages.helper import db_queries
# Note: match_algo imported lazily inside run_matching() to avoid face_recognition startup delay

router = APIRouter()


class MatchResult(BaseModel):
    status: bool
    message: Optional[str] = None
    result: Optional[dict] = None


class StatisticsResponse(BaseModel):
    totalRegistered: int
    foundCases: int
    activeCases: int
    aiMatches: int


@router.post("/matching/run", response_model=MatchResult)
async def run_matching(tolerance: float = 0.5):
    """
    Run face matching between public submissions and registered cases.
    
    - tolerance: Match threshold (0.0 to 1.0). Lower = stricter. Default 0.5
    
    Returns matched pairs: {registered_case_id: [public_submission_ids]}
    """
    try:
        # Lazy import to avoid loading face_recognition at server startup
        from pages.helper import match_algo
        
        # Run matching in thread pool to avoid blocking
        result = await run_in_threadpool(match_algo.match, tolerance=tolerance)
        
        return MatchResult(
            status=result.get("status", False),
            message=result.get("message"),
            result=result.get("result"),
        )
    except Exception as e:
        return MatchResult(
            status=False,
            message=str(e),
        )


class ConfirmMatchRequest(BaseModel):
    registered_case_id: str
    public_case_id: str


@router.post("/matching/confirm")
async def confirm_match(request: ConfirmMatchRequest):
    """
    Confirm a match between a registered case and public submission.
    Updates both records to 'Found' status.
    """
    try:
        db_queries.update_found_status(request.registered_case_id, request.public_case_id)
        return {
            "status": "confirmed",
            "registered_case_id": request.registered_case_id,
            "public_case_id": request.public_case_id,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Get dashboard statistics."""
    try:
        # Get all cases for statistics
        all_not_found = db_queries.fetch_all_not_found_registered_cases()
        
        # Count by status - we need to query the database more directly
        from pages.helper.db_queries import engine
        from pages.helper.data_models import RegisteredCases, PublicSubmissions
        from sqlmodel import Session, select, func
        
        with Session(engine) as session:
            # Total registered cases
            total_registered = session.exec(
                select(func.count(RegisteredCases.id))
            ).one()
            
            # Found cases
            found_cases = session.exec(
                select(func.count(RegisteredCases.id)).where(RegisteredCases.status == "F")
            ).one()
            
            # Active (not found) cases
            active_cases = session.exec(
                select(func.count(RegisteredCases.id)).where(RegisteredCases.status == "NF")
            ).one()
            
            # AI matches (cases with matched_with set)
            ai_matches = session.exec(
                select(func.count(RegisteredCases.id)).where(
                    RegisteredCases.matched_with.is_not(None)
                )
            ).one()
        
        return StatisticsResponse(
            totalRegistered=total_registered or 0,
            foundCases=found_cases or 0,
            activeCases=active_cases or 0,
            aiMatches=ai_matches or 0,
        )
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return StatisticsResponse(
            totalRegistered=0,
            foundCases=0,
            activeCases=0,
            aiMatches=0,
        )


@router.get("/matches")
async def get_recent_matches():
    """Get recent AI matches for dashboard display."""
    try:
        from pages.helper.db_queries import engine
        from pages.helper.data_models import RegisteredCases
        from sqlmodel import Session, select
        
        with Session(engine) as session:
            matched_cases = session.exec(
                select(RegisteredCases)
                .where(RegisteredCases.matched_with.is_not(None))
                .where(RegisteredCases.status == "NF")
                .order_by(RegisteredCases.submitted_on.desc())
                .limit(10)
            ).all()
        
        result = []
        for case in matched_cases:
            result.append({
                "id": case.id,
                "name": case.name,
                "age": case.age,
                "status": case.status,
                "matched_with": case.matched_with,
                "last_seen": case.last_seen,
            })
        
        return result
    except Exception as e:
        print(f"Error getting matches: {e}")
        return []
