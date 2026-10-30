"""
OBEPath AI - Orphan Records Cleanup Tool
Target: 78 orphan records (54 agent_logs, 24 mastery_scores referencing non-existent user_ids).
Status: PREPARATION / DRY RUN ONLY unless explicitly run with --execute.
"""

import sys
import os
import sqlite3

def run_cleanup(db_path: str, execute: bool = False):
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Exact IDs identified in investigation
    agent_orphan_ids = [
        791, 792, 813, 814, 817, 818, 876, 877, 904, 905, 976, 977, 1030, 1031, 
        1188, 1189, 1257, 1258, 1323, 1324, 1381, 1382, 1481, 1482, 1614, 1615, 
        1682, 1683, 1744, 1745, 1803, 1804, 1862, 1863, 1921, 1922, 1988, 1989, 
        2047, 2048, 2106, 2107, 2226, 2227, 2317, 2318, 2419, 2420, 2508, 2509, 
        2597, 2598, 2683, 2684
    ]

    mastery_orphan_ids = [
        27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60, 
        63, 66, 69, 72, 75, 78, 81, 84, 87, 90, 93, 96
    ]

    print(f"Mode: {'EXECUTE DELETION' if execute else 'DRY RUN (NO CHANGES)'}")
    print(f"Database target: {db_path}")

    # Check existence
    p_agent = ','.join('?' for _ in agent_orphan_ids)
    existing_agent = cur.execute(f"SELECT count(*) FROM agent_logs WHERE id IN ({p_agent})", agent_orphan_ids).fetchone()[0]

    p_mastery = ','.join('?' for _ in mastery_orphan_ids)
    existing_mastery = cur.execute(f"SELECT count(*) FROM mastery_scores WHERE id IN ({p_mastery})", mastery_orphan_ids).fetchone()[0]

    print(f"Found {existing_agent} matching orphan rows in agent_logs (target: 54).")
    print(f"Found {existing_mastery} matching orphan rows in mastery_scores (target: 24).")

    if not execute:
        print("\n[DRY RUN COMPLETE] No records were modified or deleted.")
        print("To execute deletion, this script must be called with the --execute flag.")
        conn.close()
        return

    # Deletion execution
    cur.execute(f"DELETE FROM agent_logs WHERE id IN ({p_agent})", agent_orphan_ids)
    deleted_agent = cur.rowcount

    cur.execute(f"DELETE FROM mastery_scores WHERE id IN ({p_mastery})", mastery_orphan_ids)
    deleted_mastery = cur.rowcount

    conn.commit()
    conn.close()

    print(f"\n[DELETION COMPLETE]")
    print(f"Deleted {deleted_agent} rows from agent_logs.")
    print(f"Deleted {deleted_mastery} rows from mastery_scores.")
    print(f"Total deleted: {deleted_agent + deleted_mastery} rows.")

if __name__ == "__main__":
    db_file = os.path.abspath(r"backend/obe_learning.db")
    should_execute = "--execute" in sys.argv
    run_cleanup(db_file, execute=should_execute)
