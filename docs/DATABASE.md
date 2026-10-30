# Database Architecture & Management Guide

This document outlines the database architecture, configuration, migrations, clean seeding, backup routines, and maintenance workflows for the Outcome-Based Education (OBE) Learning Platform.

---

## 1. Architecture Overview

| Environment | Engine | Configuration / URL | Purpose |
| :--- | :--- | :--- | :--- |
| **Local Development** | SQLite | `sqlite:///./obe_learning.db` | Rapid zero-dependency local dev and testing |
| **Test Suite** | SQLite / Postgres | Temporary DB via `conftest.py` (`temp_test_db_<uuid>.db`) | Clean isolated runs; never touches `obe_learning.db` |
| **Production (Neon/Render)** | PostgreSQL | `postgresql://...` (`sslmode=require`) | Scalable, ACID-compliant cloud production database |

### Connection Pooling & Free-Tier Resilience
Production configurations utilize SQLAlchemy's `QueuePool` optimized for serverless PostgreSQL providers (such as Neon):
- **URL Normalization**: Automatically converts legacy `postgres://` URLs to `postgresql://` and enforces `sslmode=require` for remote hosts.
- **Pre-Ping (`pool_pre_ping=True`)**: Detects and purges dead or dropped serverless connections before issuing queries.
- **Pool Sizing (`pool_size=5`, `max_overflow=2`)**: Protects Neon free-tier connection limits (typically 10-20 connections max).
- **Recycle (`pool_recycle=300`)**: Recycles idle pooled connections every 5 minutes to prevent stale TCP sockets.

---

## 2. Configuration & Environment Variables

Set the following environment variables in your deployment environment (e.g., Render Dashboard or `.env`):

```bash
# Production Database Connection (Neon / PostgreSQL)
DATABASE_URL=postgresql://user:password@ep-sample-123456.us-east-2.aws.neon.tech/neondb?sslmode=require

# Application Mode
ENV=production

# Server Security
ALLOWED_ORIGINS=https://your-frontend.vercel.app
SECRET_KEY=<strong-random-secret-key>
TRUST_PROXY=true
```

---

## 3. Database Migrations (Alembic)

Schema management across all environments is handled via Alembic.

### 3.1 Migration Command
To apply all pending migrations up to the latest revision:

```bash
# From backend directory
alembic upgrade head
```

Or supply an explicit database URL:
```bash
DATABASE_URL="postgresql://user:pass@host/dbname?sslmode=require" alembic upgrade head
```

### 3.2 Automated Production Startup Migration
When running in `ENV=production`, the application backend automatically executes `alembic upgrade head` inside the FastAPI `lifespan` handler before accepting client traffic. If migrations fail to apply (e.g., database unreachable or invalid credentials), startup immediately aborts with a clear descriptive error to prevent running with an incompatible schema.

### 3.3 Generating Future Migrations
When modifying models in `backend/models.py`:

```bash
cd backend
alembic revision --autogenerate -m "add_new_feature_table"
alembic upgrade head
```

---

## 4. Clean Production Curriculum Seeding

The clean curriculum seed populates **ONLY** the 4 core courses and static curriculum data:
- **4 Core Courses**: `CS101` (Python), `CS201` (Data Structures), `AI301` (Machine Learning), `CS302` (DBMS)
- **16 Course Outcomes**: 4 per course (CO1–CO4)
- **32 Topics**: 8 per course
- **27 Prerequisites**: Directed prerequisite dependency graph
- **50 Topic-Outcome Mappings**: Attainment weight distributions
- **14 Resources**: Approved curriculum documentation and tutorials
- **20 Diagnostic Questions**: 5 per course for baseline proficiency evaluation
- **281 Question Bank Items**: Practice, exercises, and assessments

> **Zero User Data**: The clean seed script creates **0** users, **0** student profiles, **0** classes, **0** enrollments, **0** attempts, **0** histories, and **0** agent logs.

### 4.1 Running the Clean Seed

```bash
# Using the default DATABASE_URL from .env:
python backend/scripts/seed_curriculum.py

# Or pointing to a specific PostgreSQL instance:
python backend/scripts/seed_curriculum.py --database-url "postgresql://user:pass@host/dbname?sslmode=require"
```

### 4.2 Idempotency Guarantee
`scripts/seed_curriculum.py` is strictly idempotent:
- Running once seeds all curriculum entities.
- Running a second time updates existing records in place and creates 0 duplicate rows.
- Reports a detailed count summary of created vs existing records.

---

## 5. Production Admin & Initial Setup

Since production databases are initialized with zero demo accounts:
1. **System Administrator Account**:
   - Provide `ADMIN_EMAIL` and `ADMIN_PASSWORD` in the production environment variables.
   - On startup, the backend automatically provisions or updates the administrative account securely.
2. **Faculty and Student Registration**:
   - Students register self-service through `/api/auth/register`.
   - Faculty accounts can be approved or provisioned by administrators via `/api/admin/users`.

---

## 6. Backup & Restore Procedures

### 6.1 Neon Point-In-Time Restore (PITR) & Branching
Neon provides native instantaneous branching and Point-In-Time Restore:
- To take a point-in-time snapshot before major updates, create a branch in the Neon console.
- In case of catastrophic failure, restore the database to any past timestamp in seconds via the Neon web console.

### 6.2 Standard PostgreSQL Backups (`pg_dump`)
To create a local SQL dump from a remote production database:

```bash
# Dump complete schema and data
pg_dump --clean --if-exists --no-owner --no-acl "postgresql://user:pass@host/dbname?sslmode=require" > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 6.3 Restoring from Backup (`psql`)
To restore an existing dump:

```bash
psql "postgresql://user:pass@host/dbname?sslmode=require" < backup_20261028_120000.sql
```

---

## 7. How to Wipe and Re-seed Production

If you need to reset a staging or production database to a completely clean slate:

```bash
# Step 1: Connect with psql and drop all public tables and types
psql "$DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO public;"

# Step 2: Apply the full Alembic baseline schema
alembic upgrade head

# Step 3: Seed the clean curriculum (0 users)
python scripts/seed_curriculum.py

# Step 4: Verify counts
python -c "from database import SessionLocal; from models import Course, Topic, QuestionBank; db = SessionLocal(); print('Courses:', db.query(Course).count(), 'Topics:', db.query(Topic).count(), 'Questions:', db.query(QuestionBank).count()); db.close()"
```

---

## 8. Test Database Isolation

All automated tests (`pytest`) are strictly isolated from development and production databases:
- **`backend/conftest.py`** automatically creates a fresh, isolated temporary SQLite database (`temp_test_db_<uuid>.db`) for each test run.
- Populates the clean curriculum schema in memory/temp file.
- Individual tests create their own transient users with unique emails and UUIDs.
- Cleans up and deletes the temporary database file on session teardown.
- **`obe_learning.db` is never modified or deleted by tests.**
