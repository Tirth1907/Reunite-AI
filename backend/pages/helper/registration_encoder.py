# ============================================================
# REGISTRATION ENCODER — DO NOT MODIFY THIS FILE
# ============================================================
# This file handles ONLY face embedding extraction for case
# registration. It is intentionally isolated from all video
# processing, fallback detection, and CCTV analysis logic.
#
# CRITICAL RULES FOR ANY FUTURE CODE CHANGES:
# 1. Do NOT add preprocessing steps to extract_registration_embedding()
# 2. Do NOT change the detector_backend from "retinaface"
# 3. Do NOT change enforce_detection to False
# 4. Do NOT add CLAHE, border detection, or any cv2 transforms
# 5. Do NOT copy patterns from video_processor.py into this file
# 6. This function must work for ALL photo types:
#    - Passport photos, outdoor photos, night photos
#    - Full body shots, selfies, WhatsApp photos
#    - Scanned photos, printed photos
# 7. If you need to improve video detection, edit video_processor.py
#    If you need to improve registration, ask first before changing
# ============================================================

import cv2
import numpy as np
from deepface import DeepFace


def extract_registration_embedding(image_bytes: bytes) -> list:
    """
    Extract ArcFace embedding from a registration photo.

    This function is the ONLY approved way to extract face embeddings
    during case registration. It is deliberately simple and robust.

    DO NOT ADD PREPROCESSING TO THIS FUNCTION.
    DO NOT CHANGE THE DETECTOR BACKEND.
    DO NOT MODIFY THIS FUNCTION WITHOUT EXPLICIT APPROVAL.

    Args:
        image_bytes: Raw bytes of the uploaded photo

    Returns:
        list: 512-dimensional ArcFace embedding vector

    Raises:
        ValueError: If no face is detected or image cannot be decoded
    """
    # Decode image bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        raise ValueError(
            "Could not decode image. Please upload a valid photo."
        )

    # Convert BGR to RGB for DeepFace
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Extract embedding — DO NOT MODIFY THESE PARAMETERS
    try:
        results = DeepFace.represent(
            img_path=img_rgb,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=True,
            align=True
        )

        if results and len(results) > 0:
            embedding = results[0]["embedding"]
            if embedding and len(embedding) == 512:
                return embedding
            raise ValueError("Invalid embedding dimensions returned.")

    except ValueError:
        raise

    except Exception:
        # RetinaFace failed — try mtcnn as fallback for registration
        # This handles unusual but valid photos
        try:
            results = DeepFace.represent(
                img_path=img_rgb,
                model_name="ArcFace",
                detector_backend="mtcnn",
                enforce_detection=True,
                align=True
            )
            if results and len(results) > 0:
                embedding = results[0]["embedding"]
                if embedding and len(embedding) == 512:
                    return embedding
        except Exception:
            pass

    raise ValueError(
        "No face detected in the image. "
        "Please upload a clear photo of the person's face."
    )
