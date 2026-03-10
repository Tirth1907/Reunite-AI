import sqlite3
import os

db_path = r'c:\Users\tirth\OneDrive\Desktop\Reunite AI 2.0\backend\sqlite_database.db'

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Checking for column 'used_fallback' in 'videouploads'...")
    cursor.execute("PRAGMA table_info(videouploads)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'used_fallback' not in columns:
        print("Adding 'used_fallback' column to 'videouploads'...")
        cursor.execute("ALTER TABLE videouploads ADD COLUMN used_fallback BOOLEAN DEFAULT 0")
    else:
        print("'used_fallback' already exists.")

    print("Checking for column 'is_low_confidence' in 'videodetections'...")
    cursor.execute("PRAGMA table_info(videodetections)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'is_low_confidence' not in columns:
        print("Adding 'is_low_confidence' column to 'videodetections'...")
        cursor.execute("ALTER TABLE videodetections ADD COLUMN is_low_confidence BOOLEAN DEFAULT 0")
    else:
        print("'is_low_confidence' already exists.")

    conn.commit()
    print("Migration completed successfully.")
except Exception as e:
    print(f"Migration failed: {e}")
finally:
    conn.close()
