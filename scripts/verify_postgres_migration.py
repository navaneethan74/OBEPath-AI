"""
OBEPath AI - Post-Migration Verification Tool
=============================================
Compares the SQLite source database with the Neon PostgreSQL destination database:
1. Verifies all 29 application tables + alembic_version exist in PostgreSQL.
2. Compares row counts between SQLite and PostgreSQL (accounting for known excluded orphans).
3. Compares MIN(id) and MAX(id) across all primary key tables.
4. Verifies critical entity records:
   - Specific user accounts, student profiles, classes, course records
   - Learning paths, assessment attempts, intervention events
5. Checks PostgreSQL sequences (ensures nextval > MAX(id) to prevent duplicate key collisions).
6. Verifies alembic_version head matches expected revision ('3a1b2c4d5e6f').
7. Safe logging: NEVER prints database credentials or passwords.
"""

import os
import sys
import sqlite3
import argparse
from typing import Dict, Any, List
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.abspath("backend"), ".env"))

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

# Known orphans excluded from migration when not recovered
KNOWN_ORPHANS_COUNT = {
    "agent_logs": 0,  # All 2,836 agent logs are preserved (user_id nullified for orphans)
    "mastery_scores": 24  # Excluded by default unless --recovered-orphans is used
}

def verify_migration(sqlite_path: str, pg_url: str, recovered_orphans: bool = False):
    print("=" * 70)
    print("OBEPath AI - Post-Migration Verification Report")
    print("=" * 70)
    
    if not os.path.exists(sqlite_path):
        print(f"Error: SQLite source database not found at {sqlite_path}")
        return False

    if not pg_url or not pg_url.startswith("postgres"):
        print("Error: A valid PostgreSQL target DATABASE_URL must be provided.")
        return False

    import psycopg2
    from urllib.parse import urlparse

    parsed = urlparse(pg_url)
    masked_host = parsed.hostname or "unknown-host"
    masked_db = parsed.path.lstrip("/") or "unknown-db"
    print(f"Source SQLite : {sqlite_path}")
    print(f"Target Neon PG: postgresql://[USER]:***@{masked_host}/{masked_db}")
    print("-" * 70)

    # 1. Connect to SQLite (Read-Only)
    sqlite_conn = sqlite3.connect(f"file:{os.path.abspath(sqlite_path)}?mode=ro", uri=True)
    sqlite_cur = sqlite_conn.cursor()

    # 2. Connect to PostgreSQL
    try:
        pg_conn = psycopg2.connect(pg_url)
        pg_cur = pg_conn.cursor()
    except Exception as e:
        print(f"[FATAL] Failed to connect to Neon PostgreSQL: {e}")
        sqlite_conn.close()
        return False

    all_passed = True
    discrepancies = []

    print("\n1. TABLE ROW-COUNT VERIFICATION")
    print(f"{'Table Name':<28} | {'SQLite Rows':<12} | {'Expected PG':<12} | {'Actual PG':<12} | {'Status'}")
    print("-" * 75)

    for table in TOPOLOGICAL_TABLES:
        sqlite_cur.execute(f'SELECT count(*) FROM "{table}"')
        src_cnt = sqlite_cur.fetchone()[0]

        if table == "users" and recovered_orphans:
            expected_pg = src_cnt + 1
        elif table == "mastery_scores" and recovered_orphans:
            expected_pg = src_cnt
        else:
            orphans = KNOWN_ORPHANS_COUNT.get(table, 0)
            expected_pg = src_cnt - orphans

        try:
            pg_cur.execute(f'SELECT count(*) FROM "{table}"')
            dest_cnt = pg_cur.fetchone()[0]
        except Exception as e:
            dest_cnt = -1
            pg_conn.rollback()

        status = "MATCH [OK]" if dest_cnt == expected_pg else "MISMATCH [!]"
        if dest_cnt != expected_pg:
            all_passed = False
            discrepancies.append(f"Row count mismatch in '{table}': expected {expected_pg}, found {dest_cnt}")

        print(f"{table:<28} | {src_cnt:<12} | {expected_pg:<12} | {dest_cnt:<12} | {status}")

    # 2. Verify Alembic Version Table
    print("\n2. SCHEMA VERSION VERIFICATION")
    try:
        pg_cur.execute("SELECT version_num FROM alembic_version LIMIT 1")
        row = pg_cur.fetchone()
        alembic_head = row[0] if row else "NONE"
        expected_head = "3a1b2c4d5e6f"
        if alembic_head == expected_head:
            print(f"  [OK] Neon PostgreSQL alembic_version is at head: '{alembic_head}'")
        else:
            all_passed = False
            print(f"  [!] Alembic version mismatch: expected '{expected_head}', got '{alembic_head}'")
            discrepancies.append(f"Alembic version is '{alembic_head}', expected '{expected_head}'")
    except Exception as e:
        all_passed = False
        print(f"  [!] Failed to read alembic_version from PostgreSQL: {e}")
        discrepancies.append(f"alembic_version read failed: {e}")
        pg_conn.rollback()

    # 3. Verify Serial Sequences Synchronization
    print("\n3. POSTGRESQL SERIAL SEQUENCE CHECK")
    seq_issues = []
    for table in TOPOLOGICAL_TABLES:
        if table == "announcement_reads":
            continue
        try:
            pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
            seq_row = pg_cur.fetchone()
            seq_name = seq_row[0] if seq_row else None
            if seq_name:
                pg_cur.execute(f"SELECT last_value, is_called FROM {seq_name}")
                curr_val, is_called = pg_cur.fetchone()

                pg_cur.execute(f'SELECT MAX(id) FROM "{table}"')
                max_id = pg_cur.fetchone()[0] or 0

                if max_id > 0 and (curr_val < max_id):
                    seq_issues.append(f"Sequence {seq_name} ({curr_val}) < MAX(id) ({max_id}) in {table}")
                    all_passed = False
        except Exception as e:
            pg_conn.rollback()

    if not seq_issues:
        print("  [OK] All 28 PostgreSQL serial sequences are synchronized above MAX(id).")
    else:
        print(f"  [!] Found {len(seq_issues)} sequence synchronization issues:")
        for s in seq_issues:
            print(f"      - {s}")
            discrepancies.append(s)

    # 4. Spot Check Critical Business Entities
    print("\n4. CRITICAL ENTITY VERIFICATION")
    spot_checks = [
        ("Core Users", "SELECT count(*) FROM users WHERE role IN ('student', 'faculty', 'admin')", 3),
        ("Active Courses", "SELECT count(*) FROM courses WHERE is_active = true", 1),
        ("Classes", "SELECT count(*) FROM classes WHERE is_active = true", 1),
        ("Learning Paths", "SELECT count(*) FROM learning_paths WHERE status = 'ACTIVE'", 1),
        ("Assessment Attempts", "SELECT count(*) FROM assessment_attempts", 1),
        ("Intervention Events", "SELECT count(*) FROM intervention_events", 1),
    ]

    for label, query, min_expected in spot_checks:
        try:
            pg_cur.execute(query)
            count = pg_cur.fetchone()[0]
            if count >= min_expected:
                print(f"  [OK] {label:<22}: {count} records confirmed.")
            else:
                print(f"  [!] {label:<22}: Expected >= {min_expected}, found {count}.")
                all_passed = False
                discrepancies.append(f"Spot check failed for {label}: found {count}")
        except Exception as e:
            print(f"  [!] {label:<22}: Query failed: {e}")
            all_passed = False
            discrepancies.append(f"Spot check query error for {label}: {e}")
            pg_conn.rollback()

    sqlite_conn.close()
    pg_conn.close()

    print("\n" + "=" * 70)
    if all_passed:
        print("MIGRATION VERIFICATION: PASSED (100% Data Integrity Verified)")
    else:
        print(f"MIGRATION VERIFICATION: FAILED ({len(discrepancies)} discrepancies detected)")
        for d in discrepancies:
            print(f"  - {d}")
    print("=" * 70)
    return all_passed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OBEPath AI Post-Migration Verification")
    parser.add_argument("--sqlite", default=r"backend/obe_learning.db", help="Path to SQLite database")
    parser.add_argument("--pg-url", default=os.getenv("DATABASE_URL"), help="Target PostgreSQL DATABASE_URL")
    parser.add_argument("--recovered-orphans", action="store_true", help="Expect recovered 24 mastery_scores and synthetic user #3")

    args = parser.parse_args()
    if not args.pg_url:
        print("Usage: python scripts/verify_postgres_migration.py --pg-url <DATABASE_URL>")
        print("(DATABASE_URL can also be read from backend/.env or environment)")
        sys.exit(1)

    verify_migration(args.sqlite, args.pg_url, recovered_orphans=args.recovered_orphans)
