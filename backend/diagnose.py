import sqlite3, json, numpy as np

conn = sqlite3.connect('sqlite_database.db')

print('=== TABLES ===')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    print(t[0])

print('\n=== VIDEO STATUS (last 3) ===')
rows = conn.execute('SELECT id, status, total_frames, processed_frames, total_detections, error_message FROM videouploads ORDER BY uploaded_at DESC LIMIT 3').fetchall()
for r in rows:
    print(r)

print('\n=== CASES AND EMBEDDINGS ===')
cases = conn.execute('SELECT id, name, face_mesh FROM registeredcases').fetchall()
for c in cases:
    if c[2]:
        arr = np.array(json.loads(c[2]))
        print(f'Name: {c[1]} | Emb len: {len(arr)} | Norm: {round(float(np.linalg.norm(arr)),3)}')
    else:
        print(f'Name: {c[1]} | Embedding: MISSING')

print('\n=== DETECTIONS ===')
dets = conn.execute('SELECT COUNT(*) FROM videodetections').fetchone()
print('Total detections in DB:', dets[0])

print('\n=== VIDEODETECTIONS COLUMNS ===')
cols = conn.execute('PRAGMA table_info(videodetections)').fetchall()
for col in cols:
    print(col)

conn.close()
