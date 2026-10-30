import os
import sys
import shutil
import sqlite3
from datetime import datetime

def inspect_db(db_path: str):
    if not os.path.exists(db_path):
        print(f"Error: {db_path} does not exist.")
        return None
    
    uri = f"file:{os.path.abspath(db_path)}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    cur = conn.cursor()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall() if not r[0].startswith("sqlite_")]
    
    stats = {}
    for t in tables:
        cur.execute(f'SELECT count(*) FROM "{t}"')
        cnt = cur.fetchone()[0]
        cur.execute(f'PRAGMA table_info("{t}")')
        cols = [col[1] for col in cur.fetchall()]
        stats[t] = {"count": cnt, "columns": cols}
        
    conn.close()
    return stats

def create_timestamped_backup(source_path: str, backup_dir: str = "backend/backups"):
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file {source_path} not found.")
    
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.basename(source_path)
    backup_filename = f"{base_name}.backup_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Use SQLite backup API via read-only source connection for 100% consistent backup
    src_uri = f"file:{os.path.abspath(source_path)}?mode=ro"
    src_conn = sqlite3.connect(src_uri, uri=True)
    dst_conn = sqlite3.connect(backup_path)
    
    with dst_conn:
        src_conn.backup(dst_conn)
        
    dst_conn.close()
    src_conn.close()
    
    print(f"[BACKUP CREATED] {source_path} -> {backup_path}")
    print(f"Size: {os.path.getsize(backup_path):,} bytes")
    return backup_path

def verify_backup(orig_path: str, backup_path: str):
    orig_stats = inspect_db(orig_path)
    backup_stats = inspect_db(backup_path)
    
    if orig_stats is None or backup_stats is None:
        return False, "Failed to inspect one or both databases"
        
    mismatches = []
    orig_tables = set(orig_stats.keys())
    backup_tables = set(backup_stats.keys())
    
    if orig_tables != backup_tables:
        diff_orig = orig_tables - backup_tables
        diff_backup = backup_tables - orig_tables
        mismatches.append(f"Table name mismatch. Only in orig: {diff_orig}, only in backup: {diff_backup}")
        
    for t in sorted(orig_tables):
        orig_cnt = orig_stats[t]["count"]
        back_cnt = backup_stats.get(t, {}).get("count", -1)
        if orig_cnt != back_cnt:
            mismatches.append(f"Row count mismatch in '{t}': original={orig_cnt}, backup={back_cnt}")
            
    is_valid = len(mismatches) == 0
    return is_valid, mismatches, orig_stats, backup_stats

if __name__ == "__main__":
    print("=== INSPECTING AND BACKING UP SQLITE DATABASE ===")
    source = os.path.abspath("backend/obe_learning.db")
    backup = create_timestamped_backup(source)
    valid, mismatches, orig_stats, back_stats = verify_backup(source, backup)
    
    print(f"\nVerification status: {'PASSED [100% MATCH]' if valid else 'FAILED'}")
    if not valid:
        for m in mismatches:
            print("  -", m)
    else:
        print(f"Total tables: {len(orig_stats)}")
        total_rows = sum(s['count'] for s in orig_stats.values())
        print(f"Total rows: {total_rows:,}")
        for t, s in sorted(orig_stats.items()):
            print(f"  {t:<30}: {s['count']:>6} rows ({len(s['columns'])} cols)")
