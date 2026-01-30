import os
import json
import logging
from pages.helper import db_queries
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def get_train_data(submitted_by: str):
    """
    Validates that training data exists for the given user.
    With face_recognition, we don't need to train a model - just verify data exists.
    """
    try:
        result = db_queries.get_training_data(submitted_by)
        if not result:
            return None, None
        
        valid_cases = 0
        for case_id, face_mesh_json in result:
            try:
                encoding = json.loads(face_mesh_json)
                if encoding and len(encoding) > 0:
                    valid_cases += 1
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid encoding for case {case_id}")
                continue
        
        return valid_cases, None
        
    except Exception as e:
        logger.error(f"Error getting training data: {e}")
        return None, str(e)
def train(submitted_by: str):
    """
    Validate data readiness for matching.
    
    With face_recognition library, we don't need to train a separate model.
    This function now just validates that face encodings exist.
    
    Returns:
        dict - {"status": bool, "message": str}
    """
    # Remove old classifier file if exists (no longer needed)
    model_name = "classifier.pkl"
    if os.path.isfile(model_name):
        os.remove(model_name)
        logger.info("Removed old classifier.pkl (no longer needed)")
    
    try:
        valid_cases, error = get_train_data(submitted_by)
        
        if error:
            return {"status": False, "message": f"Error: {error}"}
        
        if valid_cases is None or valid_cases == 0:
            return {"status": False, "message": "No valid cases found for this user"}
        
        return {
            "status": True, 
            "message": f"Ready to match! Found {valid_cases} registered cases with valid face encodings."
        }
        
    except Exception as e:
        logger.error(f"Error in train(): {e}")
        return {"status": False, "message": str(e)}
if __name__ == "__main__":
    result = train("Reunite Admin")
    print(result)