import os
import sys
import uuid
import pytest

# Ensure backend root directory is in sys.path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Generate a dedicated temporary database file for the pytest session
_TEMP_DB_FILENAME = f"temp_test_db_{uuid.uuid4().hex[:8]}.db"
_TEMP_DB_PATH = os.path.join(BACKEND_DIR, _TEMP_DB_FILENAME)
_TEMP_DB_URL = f"sqlite:///{_TEMP_DB_PATH.replace(os.sep, '/')}"

# Set DATABASE_URL and test environment before any test module is imported
os.environ["DATABASE_URL"] = _TEMP_DB_URL
os.environ["ENV"] = "test"
os.environ["ENVIRONMENT"] = "test"

import database
database.DATABASE_URL = _TEMP_DB_URL
database.engine = database.create_app_engine(_TEMP_DB_URL)
database.SessionLocal.configure(bind=database.engine)

from database import engine, SessionLocal, Base
from scripts.seed_curriculum import seed_curriculum

# Initialize tables and curriculum immediately so test collection has full schema
print(f"\n[conftest] Setting up isolated temporary test database at: {_TEMP_DB_PATH}")
Base.metadata.create_all(bind=engine)
with SessionLocal() as _seed_db:
    seed_curriculum(db=_seed_db)

@pytest.fixture(scope="session", autouse=True)
def temporary_test_database():
    """
    Session-level fixture that manages the clean, isolated temporary SQLite database
    for the test suite.
    - Disposes of the engine and removes the temp file after the test session finishes.
    """
    yield

    # Teardown: close all connections and delete the temp file
    print(f"\n[conftest] Cleaning up temporary test database: {_TEMP_DB_PATH}")
    engine.dispose()
    if os.path.exists(_TEMP_DB_PATH):
        try:
            os.remove(_TEMP_DB_PATH)
            print("[conftest] Temporary test database file removed successfully.")
        except Exception as e:
            print(f"[conftest] Warning: could not remove {_TEMP_DB_PATH}: {e}")
