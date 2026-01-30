import os
import json
import traceback
import logging
from collections import defaultdict
import numpy as np
from pages.helper import db_queries

# Setup logging
# Setup logging
logger = logging.getLogger(__name__)

# Try to import DeepFace
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    logger.warning("DeepFace not installed. Matching will fail or return empty.")

# Configurable threshold (lower = stricter matching)
# DeepFace ArcFace default for Cosine is ~0.68. Using 0.60 for stricter matching.
DEFAULT_TOLERANCE = 0.60


def calculate_cosine_distance(encoding1, encoding2):
    """Calculate Cosine distance between two face encodings."""
    a = np.array(encoding1)
    b = np.array(encoding2)
    
    # Avoid division by zero
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 1.0
        
    return 1.0 - (np.dot(a, b) / (norm_a * norm_b))


def get_public_cases_data(status="NF"):
    """Fetch public submissions with face encodings."""
    try:
        result = db_queries.fetch_public_cases(train_data=True, status=status)
        if not result:
            return None
        
        data = []
        for case_id, face_mesh_json in result:
            try:
                encoding = json.loads(face_mesh_json)
                if encoding and len(encoding) > 0:
                    data.append({"id": case_id, "encoding": np.array(encoding)})
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Skipping public case {case_id}: invalid encoding")
                continue
        
        return data if data else None
        
    except Exception as e:
        logger.error(f"Error fetching public cases: {e}")
        traceback.print_exc()
        return None


def get_registered_cases_data(status="NF"):
    """Fetch registered cases with face encodings."""
    try:
        from pages.helper.db_queries import engine
        from pages.helper.data_models import RegisteredCases
        from sqlmodel import Session, select
        
        with Session(engine) as session:
            query = select(
                RegisteredCases.id,
                RegisteredCases.face_mesh,
            ).where(RegisteredCases.status == status)
            
            result = session.exec(query).all()
        
        if not result:
            return None
        
        data = []
        for case_id, face_mesh_json in result:
            try:
                encoding = json.loads(face_mesh_json)
                if encoding and len(encoding) > 0:
                    data.append({"id": case_id, "encoding": np.array(encoding)})
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Skipping registered case {case_id}: invalid encoding")
                continue
        
        return data if data else None
        
    except Exception as e:
        logger.error(f"Error fetching registered cases: {e}")
        traceback.print_exc()
        return None


def match(tolerance: float = DEFAULT_TOLERANCE):
    """
    Match public submissions against registered cases using DeepFace embeddings (Cosine Distance).
    
    Args:
        tolerance: Maximum face distance for a match.
    
    Returns:
        dict with 'status', 'message', and 'result' (matched pairs)
    """
    if not DEEPFACE_AVAILABLE:
        return {"status": False, "message": "DeepFace library not installed"}

    matched_images = defaultdict(list)
    
    public_cases = get_public_cases_data()
    registered_cases = get_registered_cases_data()
    
    if public_cases is None or registered_cases is None:
        return {"status": False, "message": "No data available for matching"}
    
    if len(public_cases) == 0:
        return {"status": False, "message": "No public submissions to match"}
    
    if len(registered_cases) == 0:
        return {"status": False, "message": "No registered cases to match against"}
    
    # Compare each public submission against all registered cases
    for pub_case in public_cases:
        pub_id = pub_case["id"]
        pub_encoding = pub_case["encoding"]
        
        # Skip if encoding is placeholder (all zeros)
        if np.sum(pub_encoding) == 0:
            continue
            
        best_match_id = None
        min_distance = 100.0
        
        for reg_case in registered_cases:
            reg_id = reg_case["id"]
            reg_encoding = reg_case["encoding"]
            
            # Skip if encoding is placeholder
            if np.sum(reg_encoding) == 0:
                continue
                
            # Skip if dimensions mismatch (e.g. old 128 vs new 512)
            if len(reg_encoding) != len(pub_encoding):
                continue
                
            try:
                dist = calculate_cosine_distance(pub_encoding, reg_encoding)
                if dist < min_distance:
                    min_distance = dist
                    best_match_id = reg_id
            except Exception:
                continue
        
        if best_match_id and min_distance <= tolerance:
            logger.info(f"MATCH: Public {pub_id} -> Registered {best_match_id} (Dist: {min_distance:.4f})")
            
            # Persist match to database
            try:
                db_queries.update_matched_with(best_match_id, pub_id)
            except Exception as e:
                logger.error(f"Failed to persist match for {best_match_id}: {e}")

            matched_images[best_match_id].append({
                "public_id": pub_id,
                "distance": float(min_distance),
                "confidence": round((1.0 - min_distance) * 100, 2)
            })
        else:
            logger.info(f"No match for public case {pub_id} (Best Dist: {min_distance:.4f})")
    
    return {"status": True, "result": dict(matched_images)}


def match_one_against_all(case_id: str, case_type: str = "public", tolerance: float = DEFAULT_TOLERANCE):
    """
    Efficiently match a SINGLE new case against all existing cases of the opposite type.
    
    Args:
        case_id: ID of the newly submitted case.
        case_type: "public" (sighting) or "registered" (missing person).
        tolerance: Distance threshold.
    """
    logger.info(f"--- [VERIFICATION] STEP 1: Starting Incremental Match for {case_type} case: {case_id} ---")
    
    if not DEEPFACE_AVAILABLE:
        logger.error("[VERIFICATION] DeepFace NOT installed. Aborting.")
        return {"status": False, "message": "DeepFace not installed"}

    target_case = None
    candidates = []

    # 1. Fetch the Target Case and Candidates
    logger.info(f"[VERIFICATION] Fetching target case context...")
    if case_type == "public":
        # Fetch the single public case
        raw_public = db_queries.fetch_public_cases(train_data=True, status="NF")
        # Filter manually because db_queries doesn't have fetch_one_public
        for pid, mesh, *_ in raw_public:
            if pid == case_id:
                try:
                    encoding = json.loads(mesh)
                    if not encoding or np.sum(encoding) == 0:
                        logger.error("[VERIFICATION] Triggered with ZERO VECTOR encoding!")
                        return {"status": False, "message": "Invalid/Zero encoding"}
                    target_case = {"id": pid, "encoding": np.array(encoding)}
                    logger.info(f"[VERIFICATION] Found Target Public Case: {pid} (Encoding Len: {len(target_case['encoding'])})")
                    break
                except:
                    pass
        
        if not target_case:
            logger.error("[VERIFICATION] Target case NOT found in DB.")
            return {"status": False, "message": "Case not found"}
            
        # Fetch ALL registered cases as candidates
        candidates = get_registered_cases_data()
        logger.info(f"[VERIFICATION] Fetched {len(candidates) if candidates else 0} Registered Cases as candidates.")

    elif case_type == "registered":
        # Fetch the single registered case
        all_reg = get_registered_cases_data()
        if all_reg:
            for rc in all_reg:
                if rc["id"] == case_id:
                    target_case = rc
                    logger.info(f"[VERIFICATION] Found Target Registered Case: {case_id} (Encoding Len: {len(target_case['encoding'])})")
                    break
        
        if not target_case:
            logger.error("[VERIFICATION] Target case NOT found in DB.")
            return {"status": False, "message": "Case not found"}
            
        # Fetch ALL public cases as candidates
        candidates = get_public_cases_data()
        logger.info(f"[VERIFICATION] Fetched {len(candidates) if candidates else 0} Public Cases as candidates.")
    
    else:
        return {"status": False, "message": "Invalid case_type"}

    if not candidates:
        logger.info("[VERIFICATION] No candidates found for matching. Stopping.")
        return {"status": True, "result": {}}

    # 2. Run Comparison (O(N))
    logger.info(f"--- [VERIFICATION] STEP 2: Comparing against {len(candidates)} candidates ---")
    best_match_id = None
    min_distance = 100.0
    
    target_encoding = target_case["encoding"]
    
    for candidate in candidates:
        cand_id = candidate["id"]
        cand_encoding = candidate["encoding"]
        
        if len(cand_encoding) != len(target_encoding):
            continue
            
        try:
            dist = calculate_cosine_distance(target_encoding, cand_encoding)
            # Log some distances to verify logic
            if dist < 0.8: 
                 logger.info(f"[VERIFICATION] Distance Check: {case_id} vs {cand_id} = {dist:.4f}")

            if dist < min_distance:
                min_distance = dist
                best_match_id = cand_id
        except Exception:
            continue
    
    logger.info(f"[VERIFICATION] STEP 5 SANITY: Best Distance = {min_distance:.4f} (Threshold: {tolerance})")

    # 3. Handle Match
    if best_match_id and min_distance <= tolerance:
        logger.info(f"--- [VERIFICATION] STEP 3: MATCH FOUND! Persisting... ---")
        logger.info(f"MATCH: {case_id} <--> {best_match_id} (Dist: {min_distance:.4f})")
        
        # Persist match
        reg_id = best_match_id if case_type == "public" else case_id
        pub_id = case_id if case_type == "public" else best_match_id
        
        try:
            db_queries.update_matched_with(reg_id, pub_id)
            logger.info(f"[VERIFICATION] DB Update Successful for {reg_id} <--> {pub_id}")
        except Exception as e:
            logger.error(f"[VERIFICATION] Failed to persist match: {e}")
            
        return {
            "status": True,
            "match_found": True,
            "registered_id": reg_id,
            "public_id": pub_id,
            "distance": min_distance
        }
    
    logger.info(f"[VERIFICATION] No match found. Best candidate was {best_match_id} at {min_distance:.4f}")
    return {"status": True, "match_found": False}


if __name__ == "__main__":
    result = match()
    print(result)