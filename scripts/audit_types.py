import sqlite3
from datetime import datetime

conn = sqlite3.connect("file:backend/obe_learning.db?mode=ro", uri=True)
cur = conn.cursor()

time_cols = [
    ("users", "created_at"),
    ("agent_logs", "created_at"),
    ("classes", "created_at"),
    ("classes", "expires_at"),
    ("learning_paths", "generated_at"),
    ("student_profiles", "updated_at"),
    ("assessment_attempts", "created_at"),
    ("class_enrollments", "joined_at"),
    ("intervention_events", "created_at"),
    ("outcome_attainments", "updated_at"),
    ("class_resources", "created_at"),
    ("class_announcements", "created_at"),
]

print("Checking timestamp formats in SQLite:")
all_valid = True
for tbl, col in time_cols:
    rows = cur.execute(f'SELECT "{col}" FROM "{tbl}" WHERE "{col}" IS NOT NULL LIMIT 5').fetchall()
    if rows:
        sample = rows[0][0]
        # test if psycopg2 / postgres accepts this ISO format
        print(f"  {tbl:<24}.{col:<16}: {sample!r}")
        try:
            # PostgreSQL parses ISO strings like "2026-10-28 12:34:56.789000" or "2026-10-28 12:34:56"
            if isinstance(sample, str):
                datetime.fromisoformat(sample.replace(" ", "T"))
        except Exception as e:
            print(f"    [!] Warning: parse issue on {tbl}.{col}: {e}")
            all_valid = False
    else:
        print(f"  {tbl:<24}.{col:<16}: (table empty or all NULL)")

if all_valid:
    print("\n[OK] All examined timestamp strings conform to ISO-8601 compatible with PostgreSQL TIMESTAMP.")

conn.close()
