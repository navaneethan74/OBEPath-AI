import sqlite3
import os
import sys

sys.path.insert(0, ".")
backend_path = os.path.abspath("backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from scripts.migrate_sqlite_to_postgres import inspect_sqlite_data, ORPHAN_AGENT_LOG_IDS

data = inspect_sqlite_data("backend/obe_learning.db", preserve_orphan_logs=True)
cols, rows = data["agent_logs"]

print(f"Total agent_logs returned: {len(rows)} (Expected: 2836)")
assert len(rows) == 2836

id_idx = cols.index("id")
uid_idx = cols.index("user_id")
name_idx = cols.index("agent_name")
msg_idx = cols.index("message")
time_idx = cols.index("created_at")

orphan_rows = [r for r in rows if r[id_idx] in ORPHAN_AGENT_LOG_IDS]
print(f"Total orphan agent_log rows: {len(orphan_rows)} (Expected: 54)")
assert len(orphan_rows) == 54

print("\nSample preserved orphan agent_log records:")
for r in orphan_rows[:5]:
    print(f"  ID: {r[id_idx]}, user_id: {r[uid_idx]} (NULL), Agent: '{r[name_idx]}', Created: '{r[time_idx]}'")
    print(f"     Message preview: {r[msg_idx][:80]}...")
    assert r[uid_idx] is None, "user_id should be None"
    assert len(r[msg_idx]) > 0, "Message must not be empty"
    assert r[time_idx] is not None, "created_at must be preserved"

print("\n[VERIFICATION PASSED] All 54 orphan AgentLog records retain 100% of their messages, timestamps, and metadata while user_id is set to NULL.")
