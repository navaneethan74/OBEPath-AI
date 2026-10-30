from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Ensure backend/.env is loaded so standalone imports, background workers, and scripts use the configured database
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path)
else:
    load_dotenv()

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "obe_learning.db")

def normalize_database_url(url: str = None) -> str:
    """
    Normalizes DATABASE_URL for compatibility with PostgreSQL / Neon.
    - Replaces 'postgres://' with 'postgresql://'
    - Ensures sslmode=require is set for remote PostgreSQL (such as Neon)
    """
    raw_url = url or os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.replace(os.sep, '/')}")
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)

    is_pg = raw_url.startswith("postgresql://") or raw_url.startswith("postgresql+")
    if is_pg and "sslmode=" not in raw_url:
        # Remote hosts (e.g. *.neon.tech) require sslmode=require
        if "localhost" not in raw_url and "127.0.0.1" not in raw_url:
            separator = "&" if "?" in raw_url else "?"
            raw_url = f"{raw_url}{separator}sslmode=require"

    return raw_url

DATABASE_URL = normalize_database_url()

def create_app_engine(url: str = DATABASE_URL):
    """
    Creates an engine with settings appropriate for the database backend:
    - PostgreSQL: pool_pre_ping=True, small pool size for free tier (pool_size=5, max_overflow=2, pool_recycle=300)
    - SQLite: check_same_thread=False, pool_pre_ping=True
    """
    is_sqlite = "sqlite" in url
    if is_sqlite:
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True
        )
    else:
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=2,
            pool_recycle=300
        )

engine = create_app_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def sync_database_schema(eng, base):
    """Ensures SQLite tables have all columns defined in SQLAlchemy models and manages constraints."""
    if "sqlite" not in str(eng.url):
        return
    try:
        import sqlite3
        db_path = eng.url.database
        if not db_path or not os.path.exists(db_path):
            return
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for table_name, table in base.metadata.tables.items():
            cursor.execute(f"PRAGMA table_info({table_name})")
            db_cols = {row[1] for row in cursor.fetchall()}
            if not db_cols:
                continue
            for col in table.columns:
                if col.name not in db_cols:
                    col_type = "TEXT"
                    str_type = str(col.type).upper()
                    if "INT" in str_type:
                        col_type = "INTEGER"
                    elif "BOOL" in str_type:
                        col_type = "BOOLEAN"
                    elif "FLOAT" in str_type or "REAL" in str_type:
                        col_type = "REAL"
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}")

        # One-time cleanup for duplicates in outcome_attainments (keep latest row)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='outcome_attainments'")
        if cursor.fetchone():
            cursor.execute("""
                DELETE FROM outcome_attainments
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM outcome_attainments
                    GROUP BY user_id, course_id, outcome_id
                )
            """)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_user_course_outcome
                ON outcome_attainments (user_id, course_id, outcome_id)
            """)

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[sync_database_schema] Warning: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

