import json
import logging
import numpy as np
from sqlmodel import Session, select, delete
from pages.helper.db_queries import engine
from pages.helper.data_models import RegisteredCases, PublicSubmissions

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def is_zero_vector(encoding_json: str) -> bool:
    """Check if the JSON encoding represents a zero-vector."""
    try:
        encoding = json.loads(encoding_json)
        if not encoding:
            return True
        # Check if all elements are close to zero
        arr = np.array(encoding)
        if np.sum(np.abs(arr)) < 0.001:
            return True
        return False
    except Exception:
        return True

def audit_zero_vectors(dry_run=True):
    """Scan database for cases with invalid/zero face encodings."""
    logger.info(f"Starting Database Audit (Dry Run: {dry_run})")
    
    with Session(engine) as session:
        # 1. Check Registered Cases
        reg_cases = session.exec(select(RegisteredCases)).all()
        invalid_reg = []
        for case in reg_cases:
            if is_zero_vector(case.face_mesh):
                invalid_reg.append(case)
        
        logger.info(f"Found {len(invalid_reg)} Registered Cases with zero vectors.")
        for case in invalid_reg:
            logger.warning(f"[REG] Invalid: {case.id} - {case.name}")

        # 2. Check Public Submissions
        pub_cases = session.exec(select(PublicSubmissions)).all()
        invalid_pub = []
        for case in pub_cases:
            if is_zero_vector(case.face_mesh):
                invalid_pub.append(case)
        
        logger.info(f"Found {len(invalid_pub)} Public Submissions with zero vectors.")
        for case in invalid_pub:
            logger.warning(f"[PUB] Invalid: {case.id} - Loc: {case.location}")

        # 3. Action
        if not dry_run:
            if invalid_reg:
                logger.info("Deleting invalid Registered Cases...")
                for case in invalid_reg:
                    session.delete(case)
            
            if invalid_pub:
                logger.info("Deleting invalid Public Submissions...")
                for case in invalid_pub:
                    session.delete(case)
            
            session.commit()
            logger.info("Cleanup complete.")
        else:
            logger.info("Dry run complete. No data changed. Run with dry_run=False to delete.")

if __name__ == "__main__":
    # Default to dry run to be safe
    import sys
    dry_run_mode = True
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        dry_run_mode = False
    
    audit_zero_vectors(dry_run=dry_run_mode)
