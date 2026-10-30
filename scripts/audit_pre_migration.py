import os
import sys
import sqlite3

# Ensure backend root is on sys.path
backend_path = os.path.abspath("backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import models
from database import Base

def audit_schema_and_integrity(sqlite_path="backend/obe_learning.db"):
    print("=" * 70)
    print("OBEPath AI - Pre-Migration Database & Compatibility Audit")
    print("=" * 70)
    
    if not os.path.exists(sqlite_path):
        print(f"Error: {sqlite_path} does not exist!")
        return
        
    conn = sqlite3.connect(f"file:{os.path.abspath(sqlite_path)}?mode=ro", uri=True)
    cur = conn.cursor()
    
    # 1. Compare models with SQLite tables & columns
    print("\n1. SCHEMA CONSISTENCY (models.py vs SQLite)")
    model_tables = {table.name: table for table in Base.metadata.sorted_tables}
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    sqlite_tables = set(r[0] for r in cur.fetchall())
    
    print(f"Total SQLAlchemy Models : {len(model_tables)}")
    print(f"Total SQLite Tables     : {len(sqlite_tables)}")
    
    table_diff_models = set(model_tables.keys()) - sqlite_tables
    table_diff_sqlite = sqlite_tables - set(model_tables.keys()) - {"alembic_version"}
    
    if table_diff_models:
        print(f"  [!] In models.py but missing in SQLite: {table_diff_models}")
    if table_diff_sqlite:
        print(f"  [!] In SQLite but missing in models.py: {table_diff_sqlite}")
    if not table_diff_models and not table_diff_sqlite:
        print("  [OK] All 29 model tables perfectly match SQLite tables.")
        
    # Check column-level match
    col_mismatches = 0
    for t_name, t_obj in model_tables.items():
        cur.execute(f'PRAGMA table_info("{t_name}")')
        sqlite_cols = {r[1]: r[2] for r in cur.fetchall()}
        model_cols = {c.name: c for c in t_obj.columns}
        
        missing_in_sqlite = set(model_cols.keys()) - set(sqlite_cols.keys())
        missing_in_model = set(sqlite_cols.keys()) - set(model_cols.keys())
        
        if missing_in_sqlite or missing_in_model:
            col_mismatches += 1
            print(f"  Mismatch in table '{t_name}':")
            if missing_in_sqlite:
                print(f"    Missing in SQLite: {missing_in_sqlite}")
            if missing_in_model:
                print(f"    Missing in models.py: {missing_in_model}")
    if col_mismatches == 0:
        print("  [OK] All columns match between SQLAlchemy models and SQLite tables.")

    # 2. Check Referential Integrity / Foreign Keys
    print("\n2. REFERENTIAL INTEGRITY AUDIT (Foreign Key Constraints)")
    cur.execute("PRAGMA foreign_key_check")
    fk_violations = cur.fetchall()
    
    if not fk_violations:
        print("  [OK] PRAGMA foreign_key_check reported 0 violations.")
    else:
        print(f"  [!] PRAGMA foreign_key_check found {len(fk_violations)} violations:")
        for v in fk_violations[:10]:
            print(f"      Table: {v[0]}, RowId: {v[1]}, Target: {v[2]}, FK Idx: {v[3]}")
        if len(fk_violations) > 10:
            print(f"      ... and {len(fk_violations) - 10} more.")

    # Specific check on FK references to ensure Postgres won't fail
    print("\n3. DETAILED FOREIGN KEY ORPHAN ANALYSIS")
    orphan_details = {}
    
    for t_name, t_obj in model_tables.items():
        for fk in t_obj.foreign_keys:
            target_table = fk.column.table.name
            target_col = fk.column.name
            src_col = fk.parent.name
            
            # Check for orphans: src_col is not null and not in target_table(target_col)
            query = f'''
                SELECT COUNT(*) FROM "{t_name}"
                WHERE "{src_col}" IS NOT NULL 
                  AND "{src_col}" NOT IN (SELECT "{target_col}" FROM "{target_table}")
            '''
            try:
                cur.execute(query)
                row = cur.fetchone()
                count = row[0]
                if count > 0:
                    sample_ids = []
                    try:
                        cur.execute(f'SELECT id FROM "{t_name}" WHERE "{src_col}" IS NOT NULL AND "{src_col}" NOT IN (SELECT "{target_col}" FROM "{target_table}") LIMIT 15')
                        sample_ids = [r[0] for r in cur.fetchall()]
                    except Exception:
                        pass
                    orphan_details[f"{t_name}.{src_col} -> {target_table}.{target_col}"] = {
                        "table": t_name,
                        "fk_col": src_col,
                        "target_table": target_table,
                        "target_col": target_col,
                        "orphan_count": count,
                        "sample_ids": sample_ids,
                    }
            except Exception as e:
                print(f"  Error checking FK {t_name}.{src_col}: {e}")
                
    if not orphan_details:
        print("  [OK] Zero orphan records found across all foreign key relationships!")
    else:
        print(f"  [!] Found orphan records in {len(orphan_details)} relationships:")
        for rel, det in orphan_details.items():
            print(f"    - {rel}: {det['orphan_count']} orphan rows (Table '{det['table']}' IDs: {det['sample_ids']})")

    # 4. Check Unique Constraints / Duplicates
    print("\n4. UNIQUE CONSTRAINTS & DUPLICATE CHECK")
    unique_checks = [
        ("users", ["email"]),
        ("courses", ["code"]),
        ("student_profiles", ["user_id"]),
        ("classes", ["class_code"]),
        ("class_enrollments", ["class_id", "student_id"]),
        ("assessment_attempts", ["attempt_uuid"]),
        ("outcome_attainments", ["user_id", "course_id", "outcome_id"]),
    ]
    for tbl, cols in unique_checks:
        cols_str = ", ".join(f'"{c}"' for c in cols)
        q = f'SELECT {cols_str}, COUNT(*) FROM "{tbl}" GROUP BY {cols_str} HAVING COUNT(*) > 1'
        try:
            cur.execute(q)
            dups = cur.fetchall()
            if dups:
                print(f"  [!] Table '{tbl}' has {len(dups)} duplicate entries for unique key ({cols_str})!")
            else:
                print(f"  [OK] Table '{tbl}' has 0 duplicates for unique key ({cols_str}).")
        except Exception as e:
            print(f"  Error checking unique on {tbl}: {e}")

    # 5. Row Counts by Table
    print("\n5. SOURCE ROW COUNTS")
    total_rows = 0
    for t in sorted(sqlite_tables):
        cur.execute(f'SELECT count(*) FROM "{t}"')
        cnt = cur.fetchone()[0]
        total_rows += cnt
        print(f"  {t:<32}: {cnt:>6} rows")
    print(f"\nTotal SQLite Records: {total_rows:,}")
    
    conn.close()

if __name__ == "__main__":
    audit_schema_and_integrity()
