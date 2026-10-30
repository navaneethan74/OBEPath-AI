"""
OBEPath AI - Safe Read-Only Neon PostgreSQL Empty State Checker
===============================================================
Connects to Neon PostgreSQL in STRICT READ-ONLY mode and verifies
whether the database is completely empty or has existing tables.

Guarantees:
- Sets connection session to READ-ONLY (conn.set_session(readonly=True)).
- Performs zero writes, zero DDL, zero modifications.
- Never prints or exposes database passwords.
"""

import sys
import os
import argparse
from urllib.parse import urlparse

# Ensure backend root is on sys.path
backend_path = os.path.abspath("backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_path, ".env"))
from database import normalize_database_url

def check_neon_database_state(pg_url: str):
    if not pg_url or not pg_url.startswith("postgres"):
        print("Error: A valid PostgreSQL DATABASE_URL must be provided.")
        return False, []

    pg_url = normalize_database_url(pg_url)
    parsed = urlparse(pg_url)
    masked_url = f"postgresql://[USER]:***@{parsed.hostname or 'host'}/{parsed.path.lstrip('/')}"
    print("=" * 70)
    print("OBEPath AI - Neon PostgreSQL Read-Only State Check")
    print(f"Target Database: {masked_url}")
    print("=" * 70)

    import psycopg2

    try:
        # Establish connection and enforce read-only session
        conn = psycopg2.connect(pg_url)
        conn.set_session(readonly=True, autocommit=True)
        cur = conn.cursor()

        # Check existing tables in public schema
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [r[0] for r in cur.fetchall()]

        if not tables:
            print("\n[CONFIRMED EMPTY] Target Neon database contains ZERO public tables.")
            print("The database is completely clean and ready for initial schema creation and data migration.")
            conn.close()
            return True, []

        print(f"\n[NOTICE] Target database contains {len(tables)} existing tables:")
        total_rows = 0
        table_counts = {}
        for t in tables:
            cur.execute(f'SELECT count(*) FROM "{t}"')
            cnt = cur.fetchone()[0]
            table_counts[t] = cnt
            total_rows += cnt
            print(f"  - {t:<30}: {cnt:>6} rows")

        print(f"\nTotal existing records across all tables: {total_rows:,}")
        if total_rows == 0:
            print("[SAFE TO PROCEED] Schema exists but contains 0 rows of data.")
        else:
            print("[ATTENTION] Target database already contains data. Migration will use ON CONFLICT DO NOTHING.")

        conn.close()
        return len(tables) == 0 or total_rows == 0, tables

    except Exception as e:
        print(f"\n[ERROR CONNECTING TO NEON]: {e}")
        return False, []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if Neon PostgreSQL database is empty (Read-Only)")
    parser.add_argument("--pg-url", default=os.getenv("DATABASE_URL"), help="Target PostgreSQL DATABASE_URL")

    args = parser.parse_args()
    if not args.pg_url:
        print("Usage: python scripts/check_neon_empty.py --pg-url <DATABASE_URL>")
        print("(DATABASE_URL can also be read from backend/.env or environment)")
        sys.exit(1)

    check_neon_database_state(args.pg_url)
