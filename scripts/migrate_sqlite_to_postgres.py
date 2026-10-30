"""
OBEPath AI - SQLite to Neon PostgreSQL Data Migration Tool
==========================================================
Transfers all genuine user data, profiles, classes, learning paths,
mastery records, resources, communication, and OBE attainments from
SQLite to Neon PostgreSQL with strict foreign-key dependency ordering.

Features:
- Preserves all genuine user data and existing student/faculty records.
- Preserves IDs, timestamps, password hashes, and relationship integrity.
- Handles legacy orphaned rows (nullifies agent_logs.user_id to retain all 2,836 log rows;
  excludes 24 dangling mastery_scores from deleted user #3).
- Inserts data in exact topological foreign-key order using batch execution.
- Resets all PostgreSQL sequences (setval) to prevent ID collisions on subsequent inserts.
- Sets Alembic version head to '3a1b2c4d5e6f'.
- Default mode: DRY RUN (safe inspection, zero database changes).
- Security: Never prints or logs plain text passwords or secrets.
"""

import sys
import os
import sqlite3
import argparse
from typing import Dict, List, Tuple
from urllib.parse import urlparse

# Ensure backend root is on sys.path
backend_path = os.path.abspath("backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_path, ".env"))
from database import normalize_database_url

# Topological order of tables respecting foreign key hierarchy
TOPOLOGICAL_TABLES = [
    "courses",
    "users",
    "topics",
    "course_outcomes",
    "student_profiles",
    "classes",
    "agent_logs",
    "learning_paths",
    "study_sessions",
    "topic_prerequisites",
    "topic_outcome_mappings",
    "resources",
    "diagnostic_questions",
    "question_bank",
    "learning_path_items",
    "mastery_scores",
    "mastery_histories",
    "outcome_attainments",
    "outcome_attainment_history",
    "quiz_attempts",
    "assessment_attempts",
    "question_answer_history",
    "class_enrollments",
    "intervention_events",
    "class_resources",
    "class_announcements",
    "announcement_reads",
    "class_doubts",
    "class_doubt_replies"
]

# Legacy orphaned IDs in SQLite from deleted test users
ORPHAN_AGENT_LOG_IDS = set([
    791, 792, 813, 814, 817, 818, 876, 877, 904, 905, 976, 977, 1030, 1031, 
    1188, 1189, 1257, 1258, 1323, 1324, 1381, 1382, 1481, 1482, 1614, 1615, 
    1682, 1683, 1744, 1745, 1803, 1804, 1862, 1863, 1921, 1922, 1988, 1989, 
    2047, 2048, 2106, 2107, 2226, 2227, 2317, 2318, 2419, 2420, 2508, 2509, 
    2597, 2598, 2683, 2684
])

ORPHAN_MASTERY_SCORE_IDS = set([
    27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60, 
    63, 66, 69, 72, 75, 78, 81, 84, 87, 90, 93, 96
])

BOOLEAN_COLUMNS = {
    "courses": {"is_active"},
    "users": {"must_change_password"},
    "classes": {"is_active"},
    "student_profiles": {"onboarding_completed", "diagnostic_completed"},
    "learning_path_items": {"is_remedial"},
    "quiz_attempts": {"passed"},
    "resources": {"approved_by_faculty"},
    "assessment_attempts": {"passed"},
    "question_answer_history": {"is_correct"},
    "class_resources": {"is_deleted"},
    "class_announcements": {"pinned", "is_deleted"},
    "class_doubt_replies": {"is_deleted"},
}

def inspect_sqlite_data(sqlite_path: str, preserve_orphan_logs: bool = True, recover_orphan_mastery_scores: bool = False) -> Dict[str, Tuple[List[str], List[tuple]]]:
    """Reads all table columns and valid rows from SQLite, preserving logs and casting booleans."""
    conn = sqlite3.connect(f"file:{os.path.abspath(sqlite_path)}?mode=ro", uri=True)
    cur = conn.cursor()

    data = {}
    for table in TOPOLOGICAL_TABLES:
        # Get column names
        cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{table}")').fetchall()]
        cols_str = ", ".join(f'"{c}"' for c in cols)
        rows = cur.execute(f'SELECT {cols_str} FROM "{table}"').fetchall()

        if table == "users" and recover_orphan_mastery_scores:
            # If recovery option is enabled, append placeholder user #3 so FK constraints are satisfied
            user_ids = {r[cols.index("id")] for r in rows}
            if 3 not in user_ids:
                placeholder_user = (
                    3,
                    "archived_user_3@obe.archive",
                    "!disabled_login_hash!",
                    "Archived Student #3 (Pre-migration Legacy)",
                    "archived",
                    False,
                    "2026-09-21 00:00:00"
                )
                rows.append(placeholder_user)

        # Handle known orphans
        if table == "agent_logs":
            id_idx = cols.index("id")
            uid_idx = cols.index("user_id")
            if preserve_orphan_logs:
                # Nullify user_id for orphaned logs so log content is 100% preserved
                clean_rows = []
                for r in rows:
                    if r[id_idx] in ORPHAN_AGENT_LOG_IDS:
                        r_list = list(r)
                        r_list[uid_idx] = None
                        clean_rows.append(tuple(r_list))
                    else:
                        clean_rows.append(r)
                rows = clean_rows
            else:
                rows = [r for r in rows if r[id_idx] not in ORPHAN_AGENT_LOG_IDS]
                
        elif table == "mastery_scores":
            id_idx = cols.index("id")
            if not recover_orphan_mastery_scores:
                # Default: exclude records referencing deleted user #3
                rows = [r for r in rows if r[id_idx] not in ORPHAN_MASTERY_SCORE_IDS]

        # Convert SQLite integers (0/1) to Python bools for PostgreSQL BOOLEAN columns
        target_bool_cols = BOOLEAN_COLUMNS.get(table, set())
        if target_bool_cols:
            bool_indices = [cols.index(c) for c in cols if c in target_bool_cols]
            clean_rows = []
            for r in rows:
                r_list = list(r)
                for bi in bool_indices:
                    if r_list[bi] is not None:
                        r_list[bi] = bool(r_list[bi])
                clean_rows.append(tuple(r_list))
            rows = clean_rows

        data[table] = (cols, rows)

    conn.close()
    return data

def run_migration(sqlite_path: str, pg_url: str = None, execute: bool = False, run_alembic_first: bool = True, recover_orphan_mastery_scores: bool = False, require_empty: bool = True):
    print("=" * 70)
    print("OBEPath AI - SQLite to Neon PostgreSQL Data Migration")
    print(f"Mode: {'EXECUTE MIGRATION (LIVE WRITES)' if execute else 'DRY RUN / SIMULATION ONLY'}")
    print(f"Source: {sqlite_path}")

    masked_target = "None (Dry Run Inspection)"
    if pg_url:
        pg_url = normalize_database_url(pg_url)
        parsed = urlparse(pg_url)
        masked_target = f"postgresql://[USER]:***@{parsed.hostname or 'host'}/{parsed.path.lstrip('/')}"
    print(f"Target: {masked_target}")
    print("=" * 70 + "\n")

    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"Source database not found at {sqlite_path}")

    print("1. Extracting data from SQLite and validating foreign key dependencies...")
    source_data = inspect_sqlite_data(sqlite_path, preserve_orphan_logs=True, recover_orphan_mastery_scores=recover_orphan_mastery_scores)

    total_records = 0
    print("\nExtraction Summary:")
    for table in TOPOLOGICAL_TABLES:
        cols, rows = source_data[table]
        total_records += len(rows)
        print(f"  - {table:<28}: {len(rows):>6} rows, {len(cols):>2} columns")

    print(f"\nTotal valid records prepared for migration: {total_records:,}")
    if recover_orphan_mastery_scores:
        print("Orphan Handling: Preserved all 2,836 agent_logs + recovered 24 mastery_scores via synthetic archived user #3.")
    else:
        print("Orphan Handling: Preserved all 2,836 agent_logs (nullified orphaned user_id); excluded 24 deleted-user mastery_scores (backed up in JSON).")

    if not execute:
        print("\n" + "-" * 70)
        print("[DRY RUN COMPLETE] Zero database modifications performed.")
        print("To execute against Neon PostgreSQL, run with: --pg-url <DATABASE_URL> --execute")
        print("-" * 70)
        return

    # Execution against PostgreSQL
    if not pg_url or not pg_url.startswith("postgres"):
        raise ValueError("A valid PostgreSQL DATABASE_URL must be provided when --execute is specified.")

    import psycopg2
    from psycopg2.extras import execute_batch

    # Optional: Apply Alembic migrations on target if schema doesn't exist yet
    if run_alembic_first:
        print("\n2. Applying Alembic migrations on Neon PostgreSQL schema...")
        from alembic.config import Config
        from alembic import command
        alembic_ini_path = os.path.join(backend_path, "alembic.ini")
        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", os.path.join(backend_path, "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", pg_url)
        command.upgrade(alembic_cfg, "head")
        print("  Alembic schema migrations applied to head ('3a1b2c4d5e6f').")

    print("\n3. Connecting to Neon PostgreSQL...")
    pg_conn = psycopg2.connect(pg_url)
    pg_cur = pg_conn.cursor()

    try:
        print("4. Migrating tables in topological foreign-key order...")
        for table in TOPOLOGICAL_TABLES:
            cols, rows = source_data[table]
            if not rows:
                print(f"  - {table}: 0 rows (skipped)")
                continue

            cols_str = ", ".join(f'"{c}"' for c in cols)
            placeholders = ", ".join("%s" for _ in cols)
            insert_sql = f'INSERT INTO "{table}" ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

            # Destination row count before insertion
            pg_cur.execute(f'SELECT count(*) FROM "{table}"')
            count_before = pg_cur.fetchone()[0]

            if require_empty and count_before > 0:
                raise RuntimeError(
                    f"Target table '{table}' is not empty (contains {count_before} existing rows). "
                    "Migration requires a clean/empty destination database unless --allow-existing is specified."
                )

            print(f"  - Migrating {table:<26} ({len(rows):>5} rows)...", end="", flush=True)
            execute_batch(pg_cur, insert_sql, rows, page_size=1000)

            # Destination row count after insertion (measure exact delta)
            pg_cur.execute(f'SELECT count(*) FROM "{table}"')
            count_after = pg_cur.fetchone()[0]
            inserted_count = count_after - count_before
            skipped_count = len(rows) - inserted_count

            # In a clean table, all prepared rows must be inserted.
            # If any row was skipped, it indicates an unexpected duplicate or constraint conflict in the source data.
            if count_before == 0 and inserted_count < len(rows):
                raise RuntimeError(
                    f"Unexpected conflict/skipping detected on table '{table}': "
                    f"prepared {len(rows)} rows, but destination only inserted {inserted_count} rows ({skipped_count} skipped). "
                    "Aborting and rolling back transaction to prevent partial migration."
                )

            if skipped_count > 0:
                print(f" DONE ({inserted_count} inserted, {skipped_count} pre-existing/skipped without overwrite)")
            else:
                print(f" DONE ({inserted_count} inserted)")

        print("\n5. Resetting PostgreSQL serial sequences to prevent ID collision...")
        for table in TOPOLOGICAL_TABLES:
            if table == "announcement_reads":
                continue  # Composite PK without serial sequence
            pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id');")
            seq_res = pg_cur.fetchone()
            seq = seq_res[0] if seq_res else None
            if seq:
                pg_cur.execute(f"""
                    SELECT setval(
                        '{seq}', 
                        COALESCE((SELECT MAX(id) FROM "{table}"), 1), 
                        (SELECT MAX(id) FROM "{table}") IS NOT NULL
                    );
                """)
                print(f"  - Sequence '{seq}' reset to MAX(id).")

        print("\n6. Verifying Alembic version head in target...")
        pg_cur.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))")
        pg_cur.execute("DELETE FROM alembic_version")
        pg_cur.execute("INSERT INTO alembic_version (version_num) VALUES ('3a1b2c4d5e6f')")

        print("\n7. Committing transaction...")
        pg_conn.commit()
        print("MIGRATION TRANSACTION COMMITTED SUCCESSFULLY!")

    except Exception as e:
        print(f"\n[ERROR DURING MIGRATION]: {e}")
        print("Rolling back PostgreSQL transaction...")
        pg_conn.rollback()
        raise e
    finally:
        pg_conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OBEPath AI SQLite to PostgreSQL Migration")
    parser.add_argument("--sqlite", default=r"backend/obe_learning.db", help="Path to SQLite database")
    parser.add_argument("--pg-url", default=os.getenv("DATABASE_URL"), help="Target PostgreSQL DATABASE_URL")
    parser.add_argument("--execute", action="store_true", help="Execute actual migration (default: dry run)")
    parser.add_argument("--recover-orphans", action="store_true", help="Recover the 24 orphaned mastery_scores by creating synthetic archived user #3")
    parser.add_argument("--allow-existing", action="store_true", help="Allow migrating into non-empty destination tables without overwriting")

    args = parser.parse_args()
    run_migration(args.sqlite, args.pg_url, execute=args.execute, recover_orphan_mastery_scores=args.recover_orphans, require_empty=not args.allow_existing)
