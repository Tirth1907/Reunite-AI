"""
Live pipeline test - tests every stage of detection
Run from backend folder: python test_pipeline.py
"""
import sys, os, json
sys.path.insert(0, '.')

import cv2
import numpy as np

print("=" * 60)
print("STAGE 1: Check registered cases")
print("=" * 60)
import sqlite3
conn = sqlite3.connect('sqlite_database.db')
cases = conn.execute('SELECT id, name, face_mesh FROM registeredcases').fetchall()
for c in cases:
    if c[2]:
        arr = np.array(json.loads(c[2]))
        norm = float(np.linalg.norm(arr))
        print(f"  {c[1]} | norm={round(norm,3)} | {'OK' if norm > 1.0 else 'BAD EMBEDDING'}")
    else:
        print(f"  {c[1]} | NO EMBEDDING")
conn.close()

print("\n" + "=" * 60)
print("STAGE 2: Check Haar cascade")
print("=" * 60)
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
print(f"  Cascade loaded: {not cascade.empty()}")

print("\n" + "=" * 60)
print("STAGE 3: Test face detection on registered photos")
print("=" * 60)
resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
jpg_files = [f for f in os.listdir(resources_dir) if f.endswith('.jpg')][:3]
for fname in jpg_files:
    fpath = os.path.join(resources_dir, fname)
    img = cv2.imread(fpath)
    if img is None:
        print(f"  {fname}: could not load")
        continue
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60,60))
    print(f"  {fname}: Haar found {len(faces)} face(s)")
    # Also try with looser settings
    faces2 = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30,30))
    print(f"  {fname}: Haar (loose) found {len(faces2)} face(s)")

print("\n" + "=" * 60)
print("STAGE 4: Test DeepFace detection directly")
print("=" * 60)
if jpg_files:
    fpath = os.path.join(resources_dir, jpg_files[0])
    img = cv2.imread(fpath)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    try:
        from deepface import DeepFace
        results = DeepFace.represent(
            img_path=rgb,
            model_name="ArcFace",
            detector_backend="opencv",
            enforce_detection=False,
            align=True,
        )
        print(f"  DeepFace results count: {len(results)}")
        for i, r in enumerate(results):
            emb = r.get("embedding")
            area = r.get("facial_area", {})
            conf = r.get("face_confidence", 0)
            print(f"  Face {i}: conf={round(conf,3)} area={area} emb_len={len(emb) if emb else 0}")
    except Exception as e:
        print(f"  DeepFace ERROR: {e}")

print("\n" + "=" * 60)
print("STAGE 5: Test _detect_and_embed function")
print("=" * 60)
if jpg_files:
    fpath = os.path.join(resources_dir, jpg_files[0])
    img = cv2.imread(fpath)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    try:
        from pages.helper.video_processor import _detect_and_embed, _has_faces_fast
        haar_result = _has_faces_fast(rgb)
        print(f"  _has_faces_fast result: {haar_result}")
        faces = _detect_and_embed(rgb)
        print(f"  _detect_and_embed returned: {len(faces)} face(s)")
        for i, f in enumerate(faces):
            print(f"  Face {i}: emb_len={len(f[0])}, area={f[1]}, has_b64={f[2] is not None}")
    except Exception as e:
        import traceback
        print(f"  ERROR: {e}")
        traceback.print_exc()

print("\n" + "=" * 60)
print("STAGE 6: Test distance calculation")
print("=" * 60)
conn = sqlite3.connect('sqlite_database.db')
cases = conn.execute('SELECT id, name, face_mesh FROM registeredcases LIMIT 1').fetchall()
conn.close()
if cases and jpg_files:
    target_emb = np.array(json.loads(cases[0][2]))
    fpath = os.path.join(resources_dir, jpg_files[0])
    img = cv2.imread(fpath)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    try:
        from pages.helper.video_processor import _detect_and_embed
        faces = _detect_and_embed(rgb)
        if faces:
            frame_emb = np.array(faces[0][0])
            norm_a = np.linalg.norm(target_emb)
            norm_b = np.linalg.norm(frame_emb)
            if norm_a > 0 and norm_b > 0:
                distance = 1.0 - (np.dot(target_emb, frame_emb) / (norm_a * norm_b))
                print(f"  Case: {cases[0][1]}")
                print(f"  Distance: {round(distance, 4)}")
                print(f"  Threshold (Pass1): 0.40")
                print(f"  Would match: {distance <= 0.40}")
                print(f"  Would match (loose 0.65): {distance <= 0.65}")
        else:
            print("  No faces detected to compare")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nDONE")
