import sqlite3

conn = sqlite3.connect("file:backend/obe_learning.db?mode=ro", uri=True)
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() if not r[0].startswith("sqlite_")]
app_tables = [t for t in tables if t != "alembic_version"]

app_rows = sum(cur.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in app_tables)
alembic_rows = cur.execute('SELECT count(*) FROM alembic_version').fetchone()[0]
total_rows = app_rows + alembic_rows

print(f"Total SQLite rows (all 30 tables)        : {total_rows}")
print(f"Application tables rows (29 tables)       : {app_rows}")
print(f"alembic_version table rows (1 table)      : {alembic_rows}")
print(f"Application rows minus 24 orphan records : {app_rows - 24}")
print(f"Total rows in Neon (Option A + alembic)   : {app_rows - 24 + alembic_rows}")
print(f"Total rows in Neon (Option B + alembic)   : {app_rows + 1 + alembic_rows}")

conn.close()
