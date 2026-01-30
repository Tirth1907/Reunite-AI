import PIL
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Try to import DeepFace
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError as e:
    DEEPFACE_AVAILABLE = False
    logger.warning(f"DeepFace not installed: {e}. Face encoding will use placeholder.")

import tempfile
import os

def image_obj_to_numpy(image_obj) -> np.ndarray:
    """Convert an uploaded image object to a numpy array (RGB)."""
    image_obj.seek(0)  # Reset file pointer
    image = PIL.Image.open(image_obj).convert("RGB")
    return np.array(image)


def extract_face_encoding(image: np.ndarray):
    """
    Extract face encoding using DeepFace (ArcFace model).
    Returns list of floats if face found, else None.
    """
    if not DEEPFACE_AVAILABLE:
        logger.warning("DeepFace not available, returning placeholder encoding")
        return [0.0] * 512  # Placeholder encoding (ArcFace is 512-dim)
    
    try:
        # DeepFace expects a path or numpy array (BGR usually, but newer versions handle RGB)
        # However, passing numpy array directly is safest
        
        # Enforce detection to ensure a face exists
        embedding_objs = DeepFace.represent(
            img_path=image,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=True,
            align=True
        )
        
        if embedding_objs:
            # Return the embedding of the first face found
            return embedding_objs[0]["embedding"]
            
    except Exception as e:
        # DeepFace raises ValueError if face not detected with enforce_detection=True
        logger.warning(f"DeepFace extraction failed (no face or error): {e}")
        return None
    
    return None

def extract_face_mesh_landmarks(image: np.ndarray):
    """Deprecated: Use extract_face_encoding instead."""
    return extract_face_encoding(image)