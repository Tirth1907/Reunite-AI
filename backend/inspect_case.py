import sys
import json
import logging
import numpy as np
from sqlmodel import Session, select
from pages.helper.db_queries import engine
from pages.helper.data_models import RegisteredCases, PublicSubmissions

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def check_encoding(encoding_json, context):
    try:
        if not encoding_json:
            logger.info(f"[{context}] Encoding is EMPTY/NULL")
            return
            
        encoding = json.loads(encoding_json)
        arr = np.array(encoding)
        
        logger.info(f"[{context}] Encoding Length: {len(encoding)}")
        logger.info(f"[{context}] First 5 values: {arr[:5]}")
        logger.info(f"[{context}] Sum: {np.sum(arr)}")
        
        if np.sum(np.abs(arr)) < 0.001:
            logger.error(f"[{context}] ⚠️  ZERO VECTOR DETECTED! Use fix_zero_vectors.py to remove.")
        else:
            logger.info(f"[{context}] ✅ Encoding looks valid.")
            
    except Exception as e:
        logger.error(f"[{context}] Error parsing encoding: {e}")

def inspect_case(case_id):
    logger.info(f"Inspecting Case ID: {case_id}")
    
    with Session(engine) as session:
        # Check Registered
        reg_case = session.exec(select(RegisteredCases).where(RegisteredCases.id == case_id)).first()
        if reg_case:
            logger.info(f"Found in RegisteredCases: Name={reg_case.name}, Status={reg_case.status}")
            check_encoding(reg_case.face_mesh, "REG")
            if reg_case.matched_with:
                logger.info(f"Already matched with: {reg_case.matched_with}")
            else:
                logger.info("Not matched yet.")
        else:
            logger.info("Not found in RegisteredCases.")

        # Check Public
        pub_case = session.exec(select(PublicSubmissions).where(PublicSubmissions.id == case_id)).first()
        if pub_case:
            logger.info(f"Found in PublicSubmissions: Loc={pub_case.location}, Status={pub_case.status}")
            check_encoding(pub_case.face_mesh, "PUB")
        else:
            logger.info("Not found in PublicSubmissions.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_case.py <case_id>")
    else:
        inspect_case(sys.argv[1])
