import sys
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Ensure current dir is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load backend environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

from database import engine, Base, SessionLocal, get_db, sync_database_schema
from models import User
from core.security import get_current_user
from core.bootstrap import run_production_startup_checks, bootstrap_admin_if_needed
from seed_data import seed_database

# Run production startup checks before database operations
run_production_startup_checks()

from routes import (
    auth,
    courses,
    profile,
    diagnostic,
    learning_path,
    tutor,
    assessments,
    mastery_outcomes,
    faculty,
    admin,
    progress,
    student,
    class_communication
)

def run_migrations():
    """Applies Alembic migrations programmatically."""
    from alembic.config import Config
    from alembic import command
    alembic_ini_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(os.path.abspath(__file__)), "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
    command.upgrade(alembic_cfg, "head")

# Initialize DB tables
_env_val = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
_is_prod = _env_val in ("production", "prod")
_is_test = _env_val in ("test", "testing")

if _is_prod:
    try:
        run_migrations()
        print("[OBEPath Startup] Production database migrations applied successfully.")
    except Exception as exc:
        raise RuntimeError(
            f"Production startup error: Database migration failed: {exc}. "
            "Please ensure the production database is reachable and run 'alembic upgrade head'."
        ) from exc
elif not _is_test:
    # Local development with SQLite (only when not in production or test mode)
    Base.metadata.create_all(bind=engine)
    if "sqlite" in str(engine.url):
        sync_database_schema(engine, Base)
    seed_database()

# Admin Bootstrap (Render free has no shell)
_bootstrap_db = SessionLocal()
try:
    bootstrap_admin_if_needed(_bootstrap_db)
finally:
    _bootstrap_db.close()

print(f"[OBEPath Startup] Active DATABASE_URL: {engine.url.render_as_string(hide_password=True)}")

app = FastAPI(
    title="AI Learning Path Generator for Outcome-Based Education",
    description="A Generative AI and AI-Agent-Based Personalized Learning System",
    version="1.0.0"
)

from typing import Optional, List

def get_allowed_origins() -> List[str]:
    """
    Parses and validates ALLOWED_ORIGINS.
    - ALLOWED_ORIGINS must be an explicit comma-separated list.
    - Wildcard '*' is strictly rejected.
    - In ENV=production: refuses to start if ALLOWED_ORIGINS is unset, empty, or '*'.
    - In development/testing: defaults to explicit safe local origins if unset.
    """
    env_val = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    is_prod = env_val in ("production", "prod")
    cors_raw = os.getenv("ALLOWED_ORIGINS", "").strip()

    if cors_raw == "*":
        raise RuntimeError(
            "CORS configuration error: Wildcard '*' is strictly rejected in ALLOWED_ORIGINS. "
            "Please provide an explicit comma-separated list of origins."
        )

    if not cors_raw:
        if is_prod:
            raise RuntimeError(
                "CORS configuration error: ALLOWED_ORIGINS must be explicitly set in ENV=production. "
                "Wildcards and empty origins are not permitted."
            )
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]

    origins = [o.strip().rstrip("/") for o in cors_raw.split(",") if o.strip().rstrip("/")]
    if "*" in origins:
        raise RuntimeError(
            "CORS configuration error: Wildcard '*' is strictly rejected in ALLOWED_ORIGINS list."
        )

    return origins

# Configure CORS
cors_origins = get_allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.requests import Request
from starlette.responses import JSONResponse

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Production error masking: never return stack traces in production
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    env_val = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    is_prod = env_val in ("production", "prod")
    logging.exception(f"Unhandled server exception on {request.method} {request.url.path}: {exc}")
    if is_prod:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

# Register routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(profile.router)
app.include_router(diagnostic.router)
app.include_router(learning_path.router)
app.include_router(tutor.router)
app.include_router(assessments.router)
app.include_router(mastery_outcomes.router)
app.include_router(faculty.router)
app.include_router(admin.router)
app.include_router(progress.router)
app.include_router(student.router)
app.include_router(class_communication.router)

# Direct alias for /api/knowledge-map
@app.get("/api/knowledge-map")
def get_knowledge_map_direct(
    user_id: Optional[int] = None,
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from routes.mastery_outcomes import get_knowledge_map
    return get_knowledge_map(user_id=user_id, course_id=course_id, current_user=current_user, db=db)

# Direct aliases for topic details and topic resources API
@app.get("/api/topics/{topic_id}")
def api_get_topic_direct(topic_id: int, db: Session = Depends(get_db)):
    from routes.courses import get_topic_by_id
    return get_topic_by_id(topic_id, db)

@app.get("/api/topics/{topic_id}/resources")
def api_get_topic_resources_direct(topic_id: int, db: Session = Depends(get_db)):
    from routes.courses import get_topic_resources_by_id
    return get_topic_resources_by_id(topic_id, db)

@app.get("/health")
def health_check():
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "OBEPath AI API",
        "timestamp": datetime.utcnow().isoformat()
    }

# Production SPA serving: serve built React frontend if dist directory exists
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist) and os.path.exists(os.path.join(frontend_dist, "index.html")):
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse
    from fastapi import HTTPException

    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static_assets")

    from starlette.requests import Request

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    def serve_spa(full_path: str, request: Request):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json") or request.method != "GET":
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
