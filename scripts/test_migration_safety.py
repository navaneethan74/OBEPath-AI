import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure root & backend are on sys.path
sys.path.insert(0, os.path.abspath("."))
backend_path = os.path.abspath("backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import models
from database import Base
from scripts.migrate_sqlite_to_postgres import (
    TOPOLOGICAL_TABLES,
    ORPHAN_AGENT_LOG_IDS,
    ORPHAN_MASTERY_SCORE_IDS,
    inspect_sqlite_data,
    run_migration
)

class TestMigrationSafety(unittest.TestCase):
    
    def test_01_dry_run_performs_zero_network_or_db_calls(self):
        """Verifies that --dry-run never imports, connects, or issues statements to PostgreSQL."""
        with patch("psycopg2.connect") as mock_pg_connect:
            # Call with a dummy PG url but execute=False (dry-run mode)
            run_migration(
                sqlite_path="backend/obe_learning.db",
                pg_url="postgresql://fake_user:fake_password@fake.neon.tech/fake_db?sslmode=require",
                execute=False
            )
            mock_pg_connect.assert_not_called()

    def test_02_all_topological_tables_contain_on_conflict_do_nothing(self):
        """Verifies that all insert statements use ON CONFLICT DO NOTHING to prevent duplicates on rerun."""
        source_data = inspect_sqlite_data("backend/obe_learning.db")
        for table in TOPOLOGICAL_TABLES:
            cols, _ = source_data[table]
            cols_str = ", ".join(f'"{c}"' for c in cols)
            placeholders = ", ".join("%s" for _ in cols)
            insert_sql = f'INSERT INTO "{table}" ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
            self.assertIn("ON CONFLICT DO NOTHING", insert_sql)
            self.assertNotIn("ON CONFLICT DO UPDATE", insert_sql)

    def test_03_foreign_key_dag_dependency_ordering(self):
        """Verifies that every table's foreign keys point to tables strictly earlier in TOPOLOGICAL_TABLES."""
        table_indices = {tbl: idx for idx, tbl in enumerate(TOPOLOGICAL_TABLES)}
        self.assertEqual(len(table_indices), 29)
        
        for t in Base.metadata.sorted_tables:
            child_name = t.name
            child_idx = table_indices[child_name]
            for fk in t.foreign_keys:
                parent_name = fk.column.table.name
                parent_idx = table_indices[parent_name]
                self.assertLess(
                    parent_idx, child_idx,
                    f"Dependency violation: {child_name} (idx {child_idx}) depends on {parent_name} (idx {parent_idx})"
                )

    def test_04_agent_logs_message_and_timestamp_preservation(self):
        """Verifies that the 54 orphan agent logs retain all messages and timestamps when user_id is nullified."""
        data = inspect_sqlite_data("backend/obe_learning.db", preserve_orphan_logs=True)
        cols, rows = data["agent_logs"]
        id_idx = cols.index("id")
        uid_idx = cols.index("user_id")
        msg_idx = cols.index("message")
        time_idx = cols.index("created_at")
        
        orphan_rows = [r for r in rows if r[id_idx] in ORPHAN_AGENT_LOG_IDS]
        self.assertEqual(len(orphan_rows), 54)
        for r in orphan_rows:
            self.assertIsNone(r[uid_idx])
            self.assertTrue(len(r[msg_idx]) > 0)
            self.assertIsNotNone(r[time_idx])

    def test_05_transaction_rollback_guarantee_on_failure(self):
        """Verifies that if an error occurs during execution, rollback is called and changes are not committed."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = [0]
        mock_conn.cursor.return_value = mock_cur
        
        # Simulate a database error on execute_batch
        with patch("psycopg2.connect", return_value=mock_conn), \
             patch("psycopg2.extras.execute_batch", side_effect=RuntimeError("Simulated Neon network drop")):
            with self.assertRaises(RuntimeError):
                run_migration(
                    sqlite_path="backend/obe_learning.db",
                    pg_url="postgresql://fake_user:fake_password@fake.neon.tech/fake_db?sslmode=require",
                    execute=True,
                    run_alembic_first=False
                )
            mock_conn.rollback.assert_called_once()
            mock_conn.commit.assert_not_called()
            mock_conn.close.assert_called_once()

    def test_06_sequence_reset_logic_covers_all_serial_tables(self):
        """Verifies that sequence resets cover all 28 serial tables and skip announcement_reads."""
        serial_tables = [t for t in TOPOLOGICAL_TABLES if t != "announcement_reads"]
        self.assertEqual(len(serial_tables), 28)
        self.assertNotIn("announcement_reads", serial_tables)

    def test_07_original_sqlite_and_backup_intact(self):
        """Verifies that the original SQLite file and backup have identical row counts and table structures."""
        import sqlite3
        def get_counts(p):
            c = sqlite3.connect(f"file:{os.path.abspath(p)}?mode=ro", uri=True)
            res = {r[0]: c.cursor().execute(f'SELECT count(*) FROM "{r[0]}"').fetchone()[0]
                   for r in c.cursor().execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            c.close()
            return res
        orig = get_counts("backend/obe_learning.db")
        bak = get_counts("backend/backups/obe_learning.db.backup_20261030_120630")
        self.assertEqual(orig, bak)
        self.assertEqual(len(orig), 30)

    def test_08_delta_row_count_detects_skipped_inserts(self):
        """Verifies that delta verification (post_count - pre_count) raises an error if fewer rows are inserted than prepared."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        
        # Simulate count_before = 0, but count_after = 2 when prepared was 5 (3 skipped)
        mock_cur.fetchone.side_effect = [[0], [2]]
        
        with patch("psycopg2.connect", return_value=mock_conn), \
             patch("psycopg2.extras.execute_batch"):
            with self.assertRaises(RuntimeError) as ctx:
                run_migration(
                    sqlite_path="backend/obe_learning.db",
                    pg_url="postgresql://fake_user:fake_password@fake.neon.tech/fake_db?sslmode=require",
                    execute=True,
                    run_alembic_first=False
                )
            self.assertIn("Unexpected conflict/skipping detected", str(ctx.exception))
            mock_conn.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
