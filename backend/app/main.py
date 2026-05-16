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

@app.get("/api/health")
def health():
    return {"status": "ok"}

# In production (Render), serve the built frontend
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
