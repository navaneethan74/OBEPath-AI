import sqlite3

conn = sqlite3.connect("file:backend/obe_learning.db?mode=ro", uri=True)
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() if not r[0].startswith("sqlite_")]
print("Searching for any occurrences of user_id / student_id / id = 3 across all tables:")
for t in sorted(tables):
    cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
    for col in cols:
        if col in ["user_id", "student_id", "faculty_id", "created_by", "author_id", "id"]:
            if col == "id" and t != "users":
                continue
            cnt = cur.execute(f'SELECT count(*) FROM "{t}" WHERE "{col}" = 3').fetchone()[0]
            if cnt > 0:
                print(f"  {t}.{col} has {cnt} rows")

conn.close()
