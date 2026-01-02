import auth_manager
import sqlite3

# Initialize to ensure schema updates run
auth_manager.init_db()

conn = auth_manager.get_connection()
c = conn.cursor()

tables = []
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
for r in c.fetchall():
    tables.append(r[0])

print(f"Tables found: {tables}")

# Check specific tables
required = ['playback_history', 'inclusion_history']
missing = [t for t in required if t not in tables]

if missing:
    print(f"FAILED: Missing tables {missing}")
else:
    print("SUCCESS: All V2 tables present.")

conn.close()
