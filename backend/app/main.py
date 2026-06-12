import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers import auth as auth_router
from .routers import students as students_router
from .routers import events as events_router
from .routers import scores as scores_router
from .routers import admins as admins_router
from .routers import config as config_router
from .routers import student_portal as student_portal_router
from .routers import schools as schools_router
from .database import engine, Base
from . import models

app = FastAPI(title="体育成绩管理系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(students_router.router)
app.include_router(events_router.router)
app.include_router(scores_router.router)
app.include_router(admins_router.router)
app.include_router(config_router.router)
app.include_router(student_portal_router.router)
app.include_router(schools_router.router)

@app.on_event("startup")
def startup():
    from sqlalchemy import inspect, text
    # Always create tables that don't exist yet (never drops existing ones)
    Base.metadata.create_all(bind=engine)

    insp = inspect(engine)
    table_names = insp.get_table_names()

    # Safe migration: add gender column if missing
    if "scoring_standards" in table_names:
        cols = [c["name"] for c in insp.get_columns("scoring_standards")]
        if "gender" not in cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE scoring_standards ADD COLUMN gender VARCHAR(10) DEFAULT 'both'"))
                conn.commit()

    # Safe migration: add id column to system_config if missing (old schema used key as PK)
    if "system_config" in table_names:
        cols = [c["name"] for c in insp.get_columns("system_config")]
        if "id" not in cols:
            with engine.connect() as conn:
                try:
                    # Drop old PK constraint if exists (name varies)
                    try:
                        conn.execute(text("ALTER TABLE system_config DROP CONSTRAINT system_config_pkey"))
                    except Exception:
                        pass
                    conn.execute(text("ALTER TABLE system_config ADD COLUMN id SERIAL PRIMARY KEY"))
                    conn.commit()
                except Exception as e:
                    print(f"WARNING: system_config migration failed: {e}")
                    conn.rollback()
                    # Fallback: try without PK
                    try:
                        conn.execute(text("ALTER TABLE system_config ADD COLUMN id SERIAL"))
                        conn.commit()
                    except Exception:
                        conn.rollback()

    # Multi-tenancy migration: add school_id to existing tables if missing
    if "schools" not in table_names:
        with engine.connect() as conn:
            # Create schools table
            conn.execute(text("""
                CREATE TABLE schools (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL
                )
            """))
            conn.commit()

    # Add role column to admins if missing
    if "admins" in table_names:
        cols = [c["name"] for c in insp.get_columns("admins")]
        if "role" not in cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE admins ADD COLUMN role VARCHAR(20) DEFAULT 'teacher'"))
                conn.execute(text("UPDATE admins SET role = 'super' WHERE is_super = true"))
                conn.commit()

    # Check and add school_id columns to existing tables
    for tbl, nullable in [("classes", False), ("sport_events", False), ("scores", False), ("admins", True), ("system_config", False)]:
        if tbl in table_names:
            cols = [c["name"] for c in insp.get_columns(tbl)]
            if "school_id" not in cols:
                null_str = "NULL" if nullable else "NULL"
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN school_id INTEGER"))
                    conn.commit()

    # Create default school and migrate existing data if not yet done
    from .database import SessionLocal
    from .models import Admin, School

    db = SessionLocal()
    try:
        school = db.query(School).first()
        if not school:
            # Create default school from existing config or fallback
            from .models import SystemConfig
            old_name = db.query(SystemConfig).filter(SystemConfig.key == "school_name").first()
            school_name = old_name.value if old_name else "默认学校"
            # Use raw SQL to insert school since SystemConfig might have old schema
            db.execute(text(f"INSERT INTO schools (id, name) VALUES (1, :name)"), {"name": school_name})
            db.commit()

            # Assign all existing data to school 1
            db.execute(text("UPDATE classes SET school_id = 1 WHERE school_id IS NULL"))
            db.execute(text("UPDATE sport_events SET school_id = 1 WHERE school_id IS NULL"))
            db.execute(text("UPDATE scores SET school_id = 1 WHERE school_id IS NULL"))
            db.execute(text("UPDATE admins SET school_id = 1 WHERE school_id IS NULL AND is_super = false"))
            db.execute(text("UPDATE system_config SET school_id = 1 WHERE school_id IS NULL"))
            db.commit()

        # Add NOT NULL constraints and foreign keys if not present
        # (skip if already constrained - the create_all above handles new installs)
        has_fk = False
        try:
            # Check by trying to get FK info
            from sqlalchemy import inspect as sa_inspect
            fks = sa_inspect(engine).get_foreign_keys("classes")
            has_fk = any(fk.get("referred_table") == "schools" for fk in fks)
        except Exception:
            pass

        if not has_fk:
            with engine.connect() as conn:
                try:
                    conn.execute(text("ALTER TABLE classes ADD CONSTRAINT fk_classes_school FOREIGN KEY (school_id) REFERENCES schools(id)"))
                    conn.execute(text("ALTER TABLE sport_events ADD CONSTRAINT fk_events_school FOREIGN KEY (school_id) REFERENCES schools(id)"))
                    conn.execute(text("ALTER TABLE scores ADD CONSTRAINT fk_scores_school FOREIGN KEY (school_id) REFERENCES schools(id)"))
                    conn.execute(text("ALTER TABLE admins ADD CONSTRAINT fk_admins_school FOREIGN KEY (school_id) REFERENCES schools(id)"))
                    conn.execute(text("ALTER TABLE system_config ADD CONSTRAINT fk_config_school FOREIGN KEY (school_id) REFERENCES schools(id)"))
                    conn.commit()
                except Exception:
                    pass  # FK may already exist

        # Seed if no admin exists (fresh deploy)
        if not db.query(Admin).first():
            from .seed import seed
            seed()
    finally:
        db.close()

# Serve the built frontend (Render build output)
frontend_web = os.path.join(os.path.dirname(__file__), "f2k3m8")
app.mount("/assets", StaticFiles(directory=os.path.join(frontend_web, "assets")), name="assets")

def _get_index_js():
    """Scan assets for the main index-*.js bundle (largest file)."""
    assets = os.path.join(frontend_web, "assets")
    if not os.path.isdir(assets):
        return None
    candidates = [f for f in os.listdir(assets) if f.startswith("index-") and f.endswith(".js")]
    candidates.sort(key=lambda f: os.path.getsize(os.path.join(assets, f)), reverse=True)
    return candidates[0] if candidates else None

def _get_index_css():
    """Scan assets for the latest index-*.css bundle."""
    assets = os.path.join(frontend_web, "assets")
    if not os.path.isdir(assets):
        return None
    candidates = [f for f in os.listdir(assets) if f.startswith("index-") and f.endswith(".css")]
    candidates.sort(reverse=True)
    return candidates[0] if candidates else None

def _render_index_html():
    js = _get_index_js()
    css = _get_index_css()
    if not js:
        return "<html><body>Frontend not built</body></html>"
    css_tag = f'<link rel="stylesheet" crossorigin href="/assets/{css}">' if css else ''
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>体育成绩管理系统</title>
  <script type="module" crossorigin src="/assets/{js}"></script>
  {css_tag}
</head>
<body>
  <div id="app"></div>
</body>
</html>'''

PHONE_HTML = os.path.join(os.path.dirname(__file__), "phone_export.html")

@app.get("/phone")
async def phone_export():
    if os.path.isfile(PHONE_HTML):
        return FileResponse(PHONE_HTML)
    from fastapi.responses import HTMLResponse
    return HTMLResponse("<html><body><h1>phone_export.html not found</h1></body></html>")

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Not Found"}, 404)
    file_path = os.path.join(frontend_web, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    from fastapi.responses import HTMLResponse
    return HTMLResponse(_render_index_html())
