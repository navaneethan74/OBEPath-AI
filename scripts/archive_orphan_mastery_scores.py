import sqlite3
import json
import os

db_path = "backend/obe_learning.db"
conn = sqlite3.connect(f"file:{os.path.abspath(db_path)}?mode=ro", uri=True)
cur = conn.cursor()

orphan_ids = [27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60, 63, 66, 69, 72, 75, 78, 81, 84, 87, 90, 93, 96]
placeholders = ','.join('?' for _ in orphan_ids)
cur.execute('PRAGMA table_info(mastery_scores)')
cols = [c[1] for c in cur.fetchall()]

rows = cur.execute(f'SELECT * FROM mastery_scores WHERE id IN ({placeholders})', orphan_ids).fetchall()
records = [dict(zip(cols, r)) for r in rows]

os.makedirs("backend/backups", exist_ok=True)
archive_path = "backend/backups/archived_mastery_scores_user3.json"
with open(archive_path, "w", encoding="utf-8") as f:
    json.dump({
        "source": "backend/obe_learning.db",
        "description": "24 orphaned mastery_scores records referencing deleted test user_id=3",
        "record_count": len(records),
        "records": records
    }, f, indent=2)

print(f"[ARCHIVED] Successfully dumped {len(records)} orphaned mastery_scores records to {archive_path}")
conn.close()
