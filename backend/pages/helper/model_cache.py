"""
Model cache — loads ArcFace once at startup and reuses it.
Prevents repeated disk loads on every frame during video analysis.
"""
import logging
logger = logging.getLogger(__name__)

_arcface_model = None

def get_arcface_model():
    """
    Returns cached ArcFace model. Loads it on first call only.
    All subsequent calls return the same model instance.
    """
    global _arcface_model
    if _arcface_model is None:
        logger.info("[MODEL_CACHE] Loading ArcFace model for first time...")
        from deepface import DeepFace
        from deepface.commons import functions
        _arcface_model = DeepFace.build_model("ArcFace")
        logger.info("[MODEL_CACHE] ArcFace model loaded and cached.")
    return _arcface_model

def warm_up():
    """Call this at server startup to pre-load the model."""
    get_arcface_model()
    logger.info("[MODEL_CACHE] Model warm-up complete.")
