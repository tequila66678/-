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

@app.on_event("startup")
def startup():
    from sqlalchemy import inspect, text
    # Always create tables that don't exist yet (never drops existing ones)
    Base.metadata.create_all(bind=engine)

    # Safe migration: add gender column if missing (never deletes data)
    insp = inspect(engine)
    if "scoring_standards" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("scoring_standards")]
        if "gender" not in cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE scoring_standards ADD COLUMN gender VARCHAR(10) DEFAULT 'both'"))
                conn.commit()

    # Auto-seed on first deploy if no admin exists
    from .database import SessionLocal
    from .models import Admin
    db = SessionLocal()
    try:
        if not db.query(Admin).first():
            from .seed import seed
            seed()
    finally:
        db.close()

# Serve the built frontend (inside app/web/)
frontend_web = os.path.join(os.path.dirname(__file__), "web")
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

@app.get("/api/health")
def health():
    js = _get_index_js()
    return {"status": "ok", "version": "dynamic", "js": js}

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
