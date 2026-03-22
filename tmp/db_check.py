import sqlite3, json
import os

db_path = os.path.join('backend', 'sqlite_database.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('TABLES:', cur.fetchall())
cur.execute("PRAGMA table_info(videodetections)")
print('videodetections schema:', cur.fetchall())
cur.execute("PRAGMA table_info(registeredcases)")
print('registeredcases schema:', cur.fetchall())
cur.execute("SELECT COUNT(*) FROM registeredcases")
print('registered cases count:', cur.fetchone())
conn.close()
