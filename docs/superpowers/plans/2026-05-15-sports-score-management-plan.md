# 学生体育成绩管理系统 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete sports score management web app with teacher score entry (manual + voice), student self-service, statistics, and admin configuration.

**Architecture:** Python FastAPI backend with SQLAlchemy ORM, Vue 3 + Element Plus frontend, SQLite (dev) / PostgreSQL (prod). JWT for admin auth, student_id + password for student auth. Web Speech API for voice input (1.5s fixed recording).

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PyJWT, openpyxl; Vue 3, Vue Router, Element Plus, ECharts, Axios

---

## File Structure

```
backend/
  requirements.txt
  app/
    __init__.py
    main.py              # FastAPI app, CORS, mount static
    config.py             # Settings from env
    database.py           # engine, SessionLocal, Base
    models.py             # All SQLAlchemy models
    schemas.py            # All Pydantic schemas
    auth.py               # JWT create/verify, student auth helpers
    scoring.py            # Score calculation engine
    seed.py               # Preset data seeder
    routers/
      __init__.py
      auth.py             # POST /api/auth/login, GET /api/auth/me
      students.py         # CRUD + batch import/update
      events.py           # Sport events + standards CRUD
      scores.py           # Score entry, batch save, stats, export
      admins.py           # Admin account management
      config.py           # System config get/set
      student_portal.py   # Student login, scores, password, recommend
frontend/
  index.html
  package.json
  vite.config.js
  src/
    main.js
    App.vue
    router/
      index.js
    api/
      index.js            # axios instance with interceptors
    views/
      admin/
        Login.vue
        Layout.vue
        Dashboard.vue
        ScoreEntry.vue
        Students.vue
        Statistics.vue
        Settings.vue
      student/
        Login.vue
        Scores.vue
    components/
      VoiceButton.vue
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`

- [ ] **Step 1: Create backend requirements and FastAPI entry point**

Create `backend/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
alembic==1.13.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
openpyxl==3.1.5
pydantic==2.9.2
pydantic-settings==2.5.2
```

Create `backend/app/__init__.py` (empty).

Create `backend/app/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./sports.db"
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    class Config:
        env_file = ".env"

settings = Settings()
```

Create `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="体育成绩管理系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Create frontend scaffold**

Create `frontend/package.json`:
```json
{
  "name": "sports-score-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "element-plus": "^2.8.0",
    "echarts": "^5.5.0",
    "vue-echarts": "^7.0.0",
    "axios": "^1.7.0",
    "@element-plus/icons-vue": "^2.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "vite": "^5.4.0"
  }
}
```

Create `frontend/vite.config.js`:
```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

Create `frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>体育成绩管理系统</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

Create `frontend/src/main.js`:
```javascript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import axios from 'axios'

const app = createApp(App)
app.use(ElementPlus, { locale: {} })  // Chinese locale auto-detected
app.use(router)
app.mount('#app')
```

Create `frontend/src/App.vue`:
```vue
<template>
  <router-view />
</template>
```

- [ ] **Step 3: Install backend dependencies**

Run: `cd backend; pip install -r requirements.txt`
Expected: all packages install successfully

- [ ] **Step 4: Verify backend starts**

Run: `cd backend; python -m uvicorn app.main:app --reload`
Expected: Uvicorn running on http://127.0.0.1:8000

- [ ] **Step 5: Install frontend dependencies**

Run: `cd frontend; npm install`
Expected: node_modules created, no errors

- [ ] **Step 6: Verify frontend starts**

Run: `cd frontend; npm run dev`
Expected: Vite dev server on http://localhost:5173

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/app/__init__.py backend/app/main.py backend/app/config.py
git add frontend/package.json frontend/vite.config.js frontend/index.html frontend/src/main.js frontend/src/App.vue
git commit -m "feat: project scaffolding with FastAPI + Vue 3"
```

---

### Task 2: Database Models

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`

- [ ] **Step 1: Create database setup**

Create `backend/app/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: Create all models**

Create `backend/app/models.py`:
```python
from sqlalchemy import Column, Integer, String, Boolean, Date, Float, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from .database import Base
import enum

class Gender(str, enum.Enum):
    M = "M"
    F = "F"
    both = "both"

class InputFormat(str, enum.Enum):
    time_ms = "time_ms"
    decimal_seconds = "decimal_seconds"
    decimal_meters = "decimal_meters"
    integer = "integer"

class Class(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    grade = Column(String, nullable=False)        # e.g. "2027届"
    name = Column(String, nullable=False)          # e.g. "3班"
    students = relationship("Student", back_populates="class_")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(6), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    gender = Column(SqlEnum(Gender), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    password_hash = Column(String, nullable=False)
    class_ = relationship("Class", back_populates="students")
    scores = relationship("Score", back_populates="student")

class SportEvent(Base):
    __tablename__ = "sport_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    gender = Column(SqlEnum(Gender), nullable=False)
    higher_better = Column(Boolean, nullable=False)
    unit = Column(String, nullable=False)
    input_format = Column(SqlEnum(InputFormat), nullable=False)
    sort_order = Column(Integer, default=0)
    standards = relationship("ScoringStandard", back_populates="event", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="event")

class ScoringStandard(Base):
    __tablename__ = "scoring_standards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("sport_events.id"), nullable=False)
    score = Column(Integer, nullable=False)           # 1-10
    standard_value = Column(String, nullable=False)
    event = relationship("SportEvent", back_populates="standards")

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("sport_events.id"), nullable=False)
    raw_value = Column(String, nullable=False)
    earned_score = Column(Integer, nullable=False)
    test_date = Column(Date, nullable=False)
    recorder_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    student = relationship("Student", back_populates="scores")
    event = relationship("SportEvent", back_populates="scores")

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_super = Column(Boolean, default=False)
    display_name = Column(String, nullable=False)

class SystemConfig(Base):
    __tablename__ = "system_config"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
```

- [ ] **Step 3: Initialize database tables**

Run:
```python
from app.database import engine, Base
from app import models
Base.metadata.create_all(bind=engine)
```

Expected: Tables created in sports.db

- [ ] **Step 4: Commit**

```bash
git add backend/app/database.py backend/app/models.py
git commit -m "feat: database models for all entities"
```

---

### Task 3: Scoring Engine

**Files:**
- Create: `backend/app/scoring.py`

- [ ] **Step 1: Create scoring engine**

Create `backend/app/scoring.py`:
```python
"""Score calculation engine. Takes raw value + event definition, returns earned score (1-10)."""

from .models import SportEvent, ScoringStandard, InputFormat

def parse_value(raw: str, input_format: InputFormat) -> float:
    """Convert raw input string to a comparable numeric value."""
    if input_format == InputFormat.time_ms:
        # "3'30" -> (3, 30) as a float 3.30 for comparison? No - parse properly.
        # Return total seconds for comparison
        parts = raw.replace('"', '').split("'")
        minutes = int(parts[0])
        seconds = int(parts[1]) if len(parts) > 1 else 0
        return minutes * 60 + seconds
    elif input_format == InputFormat.decimal_seconds:
        return float(raw)
    elif input_format == InputFormat.decimal_meters:
        return float(raw)
    elif input_format == InputFormat.integer:
        return int(raw)
    raise ValueError(f"Unknown input_format: {input_format}")

def parse_standard_value(val: str, input_format: InputFormat) -> float:
    """Parse a standard value string the same way as parse_value."""
    return parse_value(val, input_format)

def calculate_score(raw_value: str, event: SportEvent, standards: list[ScoringStandard]) -> int:
    """Calculate earned score (1-10) using lower-score-when-between rule."""
    parsed = parse_value(raw_value, event.input_format)

    # Parse standards into (score, parsed_value) pairs sorted by score descending (10 -> 1)
    std_pairs = []
    for s in standards:
        std_pairs.append((s.score, parse_standard_value(s.standard_value, event.input_format)))

    std_pairs.sort(key=lambda x: x[0], reverse=True)  # 10, 9, ..., 1

    if event.higher_better:
        # Higher value = better. Standard values INCREASE as score goes up.
        # e.g. 跳远: 10分=1.97, 9分=1.89, ... (descending standards)
        for score, std_val in std_pairs:
            if parsed >= std_val:
                return score
    else:
        # Lower value = better. Standard values DECREASE as score goes down.
        # e.g. 50米: 10分=8.1, 9分=8.3, ... (ascending standards)
        for score, std_val in std_pairs:
            if parsed <= std_val:
                return score

    # Below minimum standard
    return 1
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/scoring.py
git commit -m "feat: scoring engine with multi-format support"
```

---

### Task 4: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas.py`

- [ ] **Step 1: Create all Pydantic schemas**

Create `backend/app/schemas.py`:
```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from .models import Gender, InputFormat

# ── Auth ──
class AdminLogin(BaseModel):
    username: str
    password: str

class AdminOut(BaseModel):
    id: int
    username: str
    display_name: str
    is_super: bool
    model_config = {"from_attributes": True}

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminOut

# ── Student ──
class StudentBase(BaseModel):
    student_id: str = Field(min_length=6, max_length=6)
    name: str
    gender: Gender
    class_id: int

class StudentCreate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int
    class_name: Optional[str] = None
    class_grade: Optional[str] = None
    model_config = {"from_attributes": True}

class StudentBatchImport(BaseModel):
    students: list[StudentCreate]

class StudentBatchUpdate(BaseModel):
    class_id: Optional[int] = None
    new_class_id: Optional[int] = None
    reset_password: bool = False

# ── Class ──
class ClassOut(BaseModel):
    id: int
    grade: str
    name: str
    model_config = {"from_attributes": True}

# ── SportEvent ──
class ScoringStandardOut(BaseModel):
    id: int
    score: int
    standard_value: str
    model_config = {"from_attributes": True}

class ScoringStandardUpdate(BaseModel):
    score: int
    standard_value: str

class SportEventCreate(BaseModel):
    name: str
    gender: Gender
    higher_better: bool
    unit: str
    input_format: InputFormat
    sort_order: int = 0

class SportEventUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[Gender] = None
    higher_better: Optional[bool] = None
    unit: Optional[str] = None
    input_format: Optional[InputFormat] = None
    sort_order: Optional[int] = None

class SportEventOut(BaseModel):
    id: int
    name: str
    gender: Gender
    higher_better: bool
    unit: str
    input_format: InputFormat
    sort_order: int
    standards: list[ScoringStandardOut] = []
    model_config = {"from_attributes": True}

# ── Score ──
class ScoreEntry(BaseModel):
    student_id: int       # DB primary key id
    event_id: int
    raw_value: str
    test_date: date

class ScoreBatchSave(BaseModel):
    scores: list[ScoreEntry]

class ScoreOut(BaseModel):
    id: int
    student_id: int
    event_id: int
    raw_value: str
    earned_score: int
    test_date: date
    model_config = {"from_attributes": True}

class ScoreWithChange(ScoreOut):
    """Score with previous comparison for display."""
    previous_score: Optional[int] = None
    change: Optional[int] = None       # positive = improvement
    is_praise: bool = False
    is_warning: bool = False

class ClassStatsQuery(BaseModel):
    class_id: int
    event_ids: Optional[list[int]] = None

class StudentStatsQuery(BaseModel):
    student_id: int
    event_ids: Optional[list[int]] = None

class EventAvgScore(BaseModel):
    event_id: int
    event_name: str
    avg_score: float

class ClassStatsOut(BaseModel):
    class_id: int
    class_name: str
    total_students: int
    avg_score: float
    excellent_rate: float   # 9-10分
    pass_rate: float         # 6分及以上
    event_avgs: list[EventAvgScore]
    warning_students: list[dict]

class StudentStatsOut(BaseModel):
    student: StudentOut
    scores_by_event: dict[str, list[ScoreOut]]  # event_name -> scores
    recommended_events: list[dict]  # top 4 events

# ── Admin ──
class AdminCreate(BaseModel):
    username: str
    password: str
    display_name: str
    is_super: bool = False

class AdminUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None

# ── Config ──
class ConfigUpdate(BaseModel):
    value: str

class ConfigOut(BaseModel):
    key: str
    value: str
    model_config = {"from_attributes": True}

# ── Student Portal ──
class StudentLogin(BaseModel):
    student_id: str
    password: str

class StudentPasswordChange(BaseModel):
    old_password: str
    new_password: str

class StudentScoreOut(BaseModel):
    event_name: str
    raw_value: str
    earned_score: int
    test_date: date
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas.py
git commit -m "feat: Pydantic schemas for all entities"
```

---

### Task 5: Auth Module

**Files:**
- Create: `backend/app/auth.py`
- Create: `backend/app/routers/__init__.py`

- [ ] **Step 1: Create auth utilities**

Create `backend/app/auth.py`:
```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import Admin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_jwt(admin_id: int, username: str) -> str:
    payload = {
        "sub": str(admin_id),
        "username": username,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Admin:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        admin_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录凭证")

    admin = db.query(Admin).get(admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="管理员不存在")
    return admin

def get_super_admin(current: Admin = Depends(get_current_admin)) -> Admin:
    if not current.is_super:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限")
    return current

def verify_student_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

Create `backend/app/routers/__init__.py` (empty).

- [ ] **Step 2: Commit**

```bash
git add backend/app/auth.py backend/app/routers/__init__.py
git commit -m "feat: JWT auth with admin and super-admin guards"
```

---

### Task 6: Admin Auth Router

**Files:**
- Create: `backend/app/routers/auth.py`

- [ ] **Step 1: Create auth router**

Create `backend/app/routers/auth.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Admin
from ..schemas import AdminLogin, AdminOut, TokenOut
from ..auth import verify_password, create_jwt, get_current_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenOut)
def login(data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == data.username).first()
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_jwt(admin.id, admin.username)
    return TokenOut(
        access_token=token,
        admin=AdminOut.model_validate(admin)
    )

@router.get("/me", response_model=AdminOut)
def me(current: Admin = Depends(get_current_admin)):
    return AdminOut.model_validate(current)
```

- [ ] **Step 2: Register router in main.py**

Edit `backend/app/main.py` after the CORS middleware block, before the health endpoint:

```python
from .routers import auth as auth_router

app.include_router(auth_router.router)
```

(Keep the existing /api/health endpoint and app definition.)

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/auth.py backend/app/main.py
git commit -m "feat: admin login/logout API"
```

---

### Task 7: Students Router

**Files:**
- Create: `backend/app/routers/students.py`

- [ ] **Step 1: Create students router**

Create `backend/app/routers/students.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Student, Class, Admin
from ..schemas import StudentCreate, StudentOut, StudentBatchUpdate
from ..auth import get_current_admin, hash_password, verify_student_password
import openpyxl
from io import BytesIO
from typing import Optional

router = APIRouter(prefix="/api/students", tags=["students"])

@router.get("", response_model=list[StudentOut])
def list_students(
    search: Optional[str] = None,
    class_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    q = db.query(Student)
    if search:
        q = q.filter(
            (Student.student_id.contains(search)) | (Student.name.contains(search))
        )
    if class_id:
        q = q.filter(Student.class_id == class_id)
    total = q.count()
    students = q.order_by(Student.student_id).offset((page - 1) * page_size).limit(page_size).all()

    # Attach class info
    result = []
    for s in students:
        out = StudentOut.model_validate(s)
        if s.class_:
            out.class_name = s.class_.name
            out.class_grade = s.class_.grade
        result.append(out)
    return result

@router.post("", response_model=StudentOut)
def create_student(data: StudentCreate, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    existing = db.query(Student).filter(Student.student_id == data.student_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="学号已存在")
    student = Student(
        student_id=data.student_id,
        name=data.name,
        gender=data.gender,
        class_id=data.class_id,
        password_hash=hash_password(data.student_id[-6:])  # default password: last 6 digits
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return StudentOut.model_validate(student)

@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    out = StudentOut.model_validate(s)
    if s.class_:
        out.class_name = s.class_.name
        out.class_grade = s.class_.grade
    return out

@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentCreate, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    s.student_id = data.student_id
    s.name = data.name
    s.gender = data.gender
    s.class_id = data.class_id
    db.commit()
    db.refresh(s)
    return StudentOut.model_validate(s)

@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    db.delete(s)
    db.commit()
    return {"ok": True}

@router.post("/batch-import")
def batch_import(file: UploadFile = File(...), db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    """Import students from Excel. Columns: 学号, 姓名, 性别, 班级(grade+name like '2027届3班')"""
    contents = file.file.read()
    wb = openpyxl.load_workbook(BytesIO(contents))
    ws = wb.active
    imported = 0
    errors = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row[0]:
            continue
        student_id = str(row[0]).strip()
        name = str(row[1]).strip()
        gender_str = str(row[2]).strip()
        class_str = str(row[3]).strip()
        gender = "M" if gender_str == "男" else "F"
        # Parse class: "2027届3班" -> grade="2027届", name="3班"
        if "届" in class_str:
            parts = class_str.split("届", 1)
            grade = parts[0] + "届"
            class_name = parts[1]
        else:
            grade = class_str
            class_name = ""
        cls = db.query(Class).filter(Class.grade == grade, Class.name == class_name).first()
        if not cls:
            cls = Class(grade=grade, name=class_name)
            db.add(cls)
            db.flush()
        existing = db.query(Student).filter(Student.student_id == student_id).first()
        if existing:
            errors.append(f"行{row_idx}: 学号{student_id}已存在，跳过")
            continue
        student = Student(
            student_id=student_id,
            name=name,
            gender=gender,
            class_id=cls.id,
            password_hash=hash_password(student_id[-6:])
        )
        db.add(student)
        imported += 1
    db.commit()
    return {"imported": imported, "errors": errors}

@router.put("/batch/update")
def batch_update(data: StudentBatchUpdate, db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    """Batch update: move students between classes or reset passwords."""
    q = db.query(Student)
    if data.class_id:
        q = q.filter(Student.class_id == data.class_id)
    students = q.all()
    count = 0
    for s in students:
        if data.new_class_id:
            s.class_id = data.new_class_id
        if data.reset_password:
            s.password_hash = hash_password(s.student_id[-6:])
        count += 1
    db.commit()
    return {"updated": count}

@router.get("/template/download")
def download_template():
    """Return Excel template for student import."""
    from fastapi.responses import StreamingResponse
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "学生信息"
    ws.append(["学号", "姓名", "性别", "班级"])
    ws.append(["270301", "张三", "女", "2027届3班"])
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=student_template.xlsx"}
    )
```

- [ ] **Step 2: Register router in main.py**

Add to `backend/app/main.py`:
```python
from .routers import students as students_router
app.include_router(students_router.router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/students.py backend/app/main.py
git commit -m "feat: student CRUD, batch import/update, template download"
```

---

### Task 8: Sport Events Router

**Files:**
- Create: `backend/app/routers/events.py`

- [ ] **Step 1: Create events router**

Create `backend/app/routers/events.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SportEvent, ScoringStandard, Admin
from ..schemas import (
    SportEventCreate, SportEventUpdate, SportEventOut,
    ScoringStandardUpdate
)
from ..auth import get_super_admin, get_current_admin

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("", response_model=list[SportEventOut])
def list_events(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    return db.query(SportEvent).order_by(SportEvent.sort_order).all()

@router.post("", response_model=SportEventOut)
def create_event(data: SportEventCreate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    event = SportEvent(**data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.put("/{event_id}", response_model=SportEventOut)
def update_event(event_id: int, data: SportEventUpdate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    event = db.query(SportEvent).get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="项目不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(event, key, val)
    db.commit()
    db.refresh(event)
    return event

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    event = db.query(SportEvent).get(event_id)
    if not event:
        raise HTTPException(status_code=404)
    db.delete(event)
    db.commit()
    return {"ok": True}

@router.put("/{event_id}/standards")
def update_standards(
    event_id: int,
    standards: list[ScoringStandardUpdate],
    db: Session = Depends(get_db),
    current: Admin = Depends(get_super_admin)
):
    event = db.query(SportEvent).get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="项目不存在")
    # Delete existing standards
    db.query(ScoringStandard).filter(ScoringStandard.event_id == event_id).delete()
    # Insert new
    for s in standards:
        std = ScoringStandard(event_id=event_id, score=s.score, standard_value=s.standard_value)
        db.add(std)
    db.commit()
    return {"ok": True, "count": len(standards)}

@router.get("/classes", response_model=list[dict])
def list_classes(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    """Return all classes for dropdowns."""
    from ..models import Class
    classes = db.query(Class).order_by(Class.grade, Class.name).all()
    return [{"id": c.id, "grade": c.grade, "name": c.name, "label": f"{c.grade}{c.name}"} for c in classes]
```

- [ ] **Step 2: Register router in main.py**

Add to `backend/app/main.py`:
```python
from .routers import events as events_router
app.include_router(events_router.router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/events.py backend/app/main.py
git commit -m "feat: sport events CRUD and scoring standards management"
```

---

### Task 9: Scores Router (Entry, Stats, Export)

**Files:**
- Create: `backend/app/routers/scores.py`

- [ ] **Step 1: Create scores router**

Create `backend/app/routers/scores.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Score, Student, SportEvent, ScoringStandard, Class, Admin
from ..schemas import ScoreBatchSave, ScoreEntry, ScoreWithChange
from ..auth import get_current_admin
from ..scoring import calculate_score
from ..config import settings
import openpyxl
from io import BytesIO
from datetime import date
from typing import Optional
from collections import defaultdict

router = APIRouter(prefix="/api/scores", tags=["scores"])

def _get_previous_score(db: Session, student_db_id: int, event_id: int, current_date: date) -> Optional[Score]:
    """Get the most recent score before current_date."""
    return (
        db.query(Score)
        .filter(
            Score.student_id == student_db_id,
            Score.event_id == event_id,
            Score.test_date < current_date
        )
        .order_by(Score.test_date.desc())
        .first()
    )

@router.post("/batch", response_model=list[ScoreWithChange])
def batch_save_scores(
    data: ScoreBatchSave,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    results = []
    praise_threshold = 1  # default
    warning_threshold = 2  # default
    from ..models import SystemConfig
    praise_cfg = db.query(SystemConfig).filter(SystemConfig.key == "praise_threshold").first()
    warning_cfg = db.query(SystemConfig).filter(SystemConfig.key == "warning_threshold").first()
    if praise_cfg:
        praise_threshold = int(praise_cfg.value)
    if warning_cfg:
        warning_threshold = int(warning_cfg.value)

    for entry in data.scores:
        event = db.query(SportEvent).get(entry.event_id)
        standards = db.query(ScoringStandard).filter(ScoringStandard.event_id == entry.event_id).all()

        earned = calculate_score(entry.raw_value, event, standards)

        prev = _get_previous_score(db, entry.student_id, entry.event_id, entry.test_date)
        prev_score = None
        change = None
        is_praise = False
        is_warning = False
        if prev:
            prev_score = prev.earned_score
            change = earned - prev_score
            is_praise = change >= praise_threshold
            is_warning = (prev_score - earned) >= warning_threshold

        # Upsert: if score exists for same student+event+date, update
        existing = (
            db.query(Score)
            .filter(
                Score.student_id == entry.student_id,
                Score.event_id == entry.event_id,
                Score.test_date == entry.test_date
            ).first()
        )
        if existing:
            existing.raw_value = entry.raw_value
            existing.earned_score = earned
            existing.recorder_id = current.id
            score_obj = existing
        else:
            score_obj = Score(
                student_id=entry.student_id,
                event_id=entry.event_id,
                raw_value=entry.raw_value,
                earned_score=earned,
                test_date=entry.test_date,
                recorder_id=current.id
            )
            db.add(score_obj)

        db.flush()
        db.refresh(score_obj)

        result = ScoreWithChange(
            id=score_obj.id,
            student_id=score_obj.student_id,
            event_id=score_obj.event_id,
            raw_value=score_obj.raw_value,
            earned_score=score_obj.earned_score,
            test_date=score_obj.test_date,
            previous_score=prev_score,
            change=change,
            is_praise=is_praise,
            is_warning=is_warning,
        )
        results.append(result)

    db.commit()
    return results

@router.get("/class-stats")
def class_stats(
    class_id: int = Query(...),
    event_ids: Optional[str] = Query(None),  # comma-separated
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    cls = db.query(Class).get(class_id)
    if not cls:
        raise HTTPException(404, "班级不存在")

    event_id_list = [int(x) for x in event_ids.split(",")] if event_ids else None

    students = db.query(Student).filter(Student.class_id == class_id).all()
    scores_q = db.query(Score).filter(
        Score.student_id.in_([s.id for s in students])
    )
    if event_id_list:
        scores_q = scores_q.filter(Score.event_id.in_(event_id_list))

    # Get latest score per student per event
    all_scores = scores_q.order_by(Score.test_date.desc()).all()
    latest = {}
    for sc in all_scores:
        key = (sc.student_id, sc.event_id)
        if key not in latest:
            latest[key] = sc

    events = db.query(SportEvent).all()
    if event_id_list:
        events = [e for e in events if e.id in event_id_list]

    # Averages per event
    event_scores = defaultdict(list)
    student_totals = defaultdict(list)
    for (sid, eid), sc in latest.items():
        event_scores[eid].append(sc.earned_score)
        student_totals[sid].append(sc.earned_score)

    event_avgs = []
    for e in events:
        scores_list = event_scores.get(e.id, [])
        avg = sum(scores_list) / len(scores_list) if scores_list else 0
        event_avgs.append({"event_id": e.id, "event_name": e.name, "avg_score": round(avg, 1)})

    total_scores = [sum(v) for v in student_totals.values() if v]
    max_per_student = len(events)
    overall_avg = sum(total_scores) / len(total_scores) if total_scores else 0
    excellent_count = sum(1 for t in total_scores if t / max_per_student >= 9) if max_per_student > 0 else 0
    pass_count = sum(1 for t in total_scores if t / max_per_student >= 6) if max_per_student > 0 else 0
    n_students = len(student_totals)

    # Warning students
    warning_students = []
    for s in students:
        for e in events:
            prev = None
            student_scores = sorted(
                [sc for sc in all_scores if sc.student_id == s.id and sc.event_id == e.id],
                key=lambda x: x.test_date
            )
            if len(student_scores) >= 2:
                prev = student_scores[-2].earned_score
                curr = student_scores[-1].earned_score
                if prev - curr >= 2:
                    warning_students.append({
                        "student_id": s.id,
                        "student_name": s.name,
                        "student_no": s.student_id,
                        "event_name": e.name,
                        "prev_score": prev,
                        "curr_score": curr
                    })

    return {
        "class_id": class_id,
        "class_name": f"{cls.grade}{cls.name}",
        "total_students": n_students,
        "avg_score": round(overall_avg, 1),
        "excellent_rate": round(excellent_count / n_students * 100, 1) if n_students else 0,
        "pass_rate": round(pass_count / n_students * 100, 1) if n_students else 0,
        "event_avgs": event_avgs,
        "warning_students": warning_students
    }

@router.get("/student-stats/{student_id}")
def student_stats(
    student_id: int,
    event_ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(404, "学生不存在")

    event_id_list = [int(x) for x in event_ids.split(",")] if event_ids else None
    scores_q = db.query(Score).filter(Score.student_id == student_id)
    if event_id_list:
        scores_q = scores_q.filter(Score.event_id.in_(event_id_list))

    all_scores = scores_q.order_by(Score.test_date.desc()).all()

    scores_by_event = defaultdict(list)
    for sc in all_scores:
        event = db.query(SportEvent).get(sc.event_id)
        scores_by_event[event.name].append({
            "id": sc.id,
            "raw_value": sc.raw_value,
            "earned_score": sc.earned_score,
            "test_date": sc.test_date.isoformat()
        })

    # Recommend top 4 events
    latest_per_event = {}
    for sc in all_scores:
        if sc.event_id not in latest_per_event:
            latest_per_event[sc.event_id] = sc

    recs = sorted(latest_per_event.items(), key=lambda x: x[1].earned_score, reverse=True)[:4]
    recommended = []
    medals = ["🥇", "🥈", "🥉", "④"]
    for i, (eid, sc) in enumerate(recs):
        event = db.query(SportEvent).get(eid)
        recommended.append({
            "rank": i + 1,
            "medal": medals[i],
            "event_name": event.name,
            "score": sc.earned_score
        })

    return {
        "student": {
            "id": s.id,
            "student_id": s.student_id,
            "name": s.name,
            "gender": s.gender.value,
            "class_name": s.class_.name if s.class_ else "",
            "class_grade": s.class_.grade if s.class_ else "",
        },
        "scores_by_event": dict(scores_by_event),
        "recommended_events": recommended
    }

@router.get("/export/class")
def export_class_scores(
    class_id: int = Query(...),
    event_ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    cls = db.query(Class).get(class_id)
    students = db.query(Student).filter(Student.class_id == class_id).order_by(Student.student_id).all()
    event_id_list = [int(x) for x in event_ids.split(",")] if event_ids else None
    events_q = db.query(SportEvent)
    if event_id_list:
        events_q = events_q.filter(SportEvent.id.in_(event_id_list))
    events = events_q.order_by(SportEvent.sort_order).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{cls.grade}{cls.name}成绩"
    headers = ["学号", "姓名", "性别"] + [e.name for e in events] + ["总分"]
    ws.append(headers)

    for s in students:
        row = [s.student_id, s.name, "男" if s.gender.value == "M" else "女"]
        total = 0
        for e in events:
            latest = (
                db.query(Score)
                .filter(Score.student_id == s.id, Score.event_id == e.id)
                .order_by(Score.test_date.desc())
                .first()
            )
            if latest:
                row.append(latest.earned_score)
                total += latest.earned_score
            else:
                row.append("-")
        row.append(total)
        ws.append(row)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={cls.grade}{cls.name}_scores.xlsx"}
    )

@router.get("/export/student/{student_id}")
def export_student_scores(
    student_id: int,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(404)

    wb = openpyxl.Workbook()
    # Sheet 1: Current summary
    ws1 = wb.active
    ws1.title = "成绩汇总"
    ws1.append(["项目", "成绩", "得分", "测试日期"])
    events = db.query(SportEvent).order_by(SportEvent.sort_order).all()
    total = 0
    for e in events:
        latest = (
            db.query(Score)
            .filter(Score.student_id == student_id, Score.event_id == e.id)
            .order_by(Score.test_date.desc())
            .first()
        )
        if latest:
            ws1.append([e.name, latest.raw_value, latest.earned_score, latest.test_date.isoformat()])
            total += latest.earned_score
        else:
            ws1.append([e.name, "-", "-", "-"])
    ws1.append(["总分", "", total, ""])

    # Sheet 2: History
    ws2 = wb.create_sheet("历史记录")
    ws2.append(["项目", "成绩", "得分", "测试日期"])
    scores = db.query(Score).filter(Score.student_id == student_id).order_by(Score.test_date.desc()).all()
    for sc in scores:
        event = db.query(SportEvent).get(sc.event_id)
        ws2.append([event.name, sc.raw_value, sc.earned_score, sc.test_date.isoformat()])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={s.name}_{s.student_id}_scores.xlsx"}
    )

@router.get("/student-list/{class_id}")
def get_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    """Return students in a class for score entry."""
    students = (
        db.query(Student)
        .filter(Student.class_id == class_id)
        .order_by(Student.student_id)
        .all()
    )
    return [{"id": s.id, "student_id": s.student_id, "name": s.name, "gender": s.gender.value} for s in students]
```

- [ ] **Step 2: Register router in main.py**

Add to `backend/app/main.py`:
```python
from .routers import scores as scores_router
app.include_router(scores_router.router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/scores.py backend/app/main.py
git commit -m "feat: score batch save, class stats, student stats, Excel export"
```

---

### Task 10: Admins & Config Routers

**Files:**
- Create: `backend/app/routers/admins.py`
- Create: `backend/app/routers/config.py`

- [ ] **Step 1: Create admins router**

Create `backend/app/routers/admins.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Admin
from ..schemas import AdminCreate, AdminUpdate, AdminOut
from ..auth import get_super_admin, hash_password

router = APIRouter(prefix="/api/admins", tags=["admins"])

@router.get("", response_model=list[AdminOut])
def list_admins(db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    return db.query(Admin).all()

@router.post("", response_model=AdminOut)
def create_admin(data: AdminCreate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    existing = db.query(Admin).filter(Admin.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    admin = Admin(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        is_super=data.is_super
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return AdminOut.model_validate(admin)

@router.put("/{admin_id}", response_model=AdminOut)
def update_admin(admin_id: int, data: AdminUpdate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    admin = db.query(Admin).get(admin_id)
    if not admin:
        raise HTTPException(404, "管理员不存在")
    if data.display_name is not None:
        admin.display_name = data.display_name
    if data.password is not None:
        admin.password_hash = hash_password(data.password)
    db.commit()
    db.refresh(admin)
    return AdminOut.model_validate(admin)

@router.delete("/{admin_id}")
def delete_admin(admin_id: int, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    admin = db.query(Admin).get(admin_id)
    if not admin:
        raise HTTPException(404)
    if admin.id == current.id:
        raise HTTPException(400, detail="不能删除自己")
    db.delete(admin)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Create config router**

Create `backend/app/routers/config.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SystemConfig, Admin
from ..schemas import ConfigUpdate, ConfigOut
from ..auth import get_super_admin

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("", response_model=list[ConfigOut])
def list_config(db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    return db.query(SystemConfig).all()

@router.get("/public")
def get_public_config(db: Session = Depends(get_db)):
    """Public config (school_name, designer) - no auth needed."""
    configs = db.query(SystemConfig).all()
    result = {}
    for c in configs:
        if c.key in ("school_name", "designer"):
            result[c.key] = c.value
    return result

@router.put("/{key}")
def update_config(key: str, data: ConfigUpdate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        config = SystemConfig(key=key, value=data.value)
        db.add(config)
    else:
        config.value = data.value
    db.commit()
    return {"ok": True, "key": key, "value": data.value}
```

- [ ] **Step 3: Register routers in main.py**

Add to `backend/app/main.py`:
```python
from .routers import admins as admins_router
from .routers import config as config_router
app.include_router(admins_router.router)
app.include_router(config_router.router)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/admins.py backend/app/routers/config.py backend/app/main.py
git commit -m "feat: admin management and system config APIs"
```

---

### Task 11: Student Portal Router

**Files:**
- Create: `backend/app/routers/student_portal.py`

- [ ] **Step 1: Create student portal router**

Create `backend/app/routers/student_portal.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Student, Score, SportEvent
from ..schemas import StudentLogin, StudentPasswordChange
from ..auth import hash_password, verify_student_password
from collections import defaultdict

router = APIRouter(prefix="/api/student", tags=["student-portal"])

def _authenticate_student(db: Session, student_id: str, password: str) -> Student:
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student or not verify_student_password(password, student.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="学号或密码错误")
    return student

@router.post("/login")
def student_login(data: StudentLogin, db: Session = Depends(get_db)):
    student = _authenticate_student(db, data.student_id, data.password)
    return {
        "token": f"student_{student.id}",  # simple token for student session
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name,
            "gender": student.gender.value,
            "class_name": student.class_.name if student.class_ else "",
            "class_grade": student.class_.grade if student.class_ else "",
        }
    }

@router.get("/scores")
def get_my_scores(student_id: str, token: str, db: Session = Depends(get_db)):
    """Get all scores for a student. Token is 'student_{id}' from login."""
    expected_token = f"student_"
    if not token.startswith(expected_token):
        raise HTTPException(401, "无效的登录凭证")
    db_id = int(token.split("_")[1])
    student = db.query(Student).get(db_id)
    if not student or student.student_id != student_id:
        raise HTTPException(401, "无效的登录凭证")

    scores = db.query(Score).filter(Score.student_id == db_id).order_by(Score.test_date.desc()).all()
    events = {e.id: e for e in db.query(SportEvent).all()}

    # Group by test_date
    by_date = defaultdict(list)
    for sc in scores:
        by_date[sc.test_date.isoformat()].append({
            "event_name": events[sc.event_id].name if sc.event_id in events else "未知",
            "raw_value": sc.raw_value,
            "earned_score": sc.earned_score
        })

    # Current scores (latest per event)
    latest = {}
    for sc in scores:
        if sc.event_id not in latest:
            latest[sc.event_id] = sc

    current = []
    total = 0
    for eid, sc in latest.items():
        current.append({
            "event_name": events[eid].name if eid in events else "未知",
            "raw_value": sc.raw_value,
            "earned_score": sc.earned_score,
            "test_date": sc.test_date.isoformat()
        })
        total += sc.earned_score

    # Recommendations (top 4)
    recs = sorted(latest.items(), key=lambda x: x[1].earned_score, reverse=True)[:4]
    medals = ["🥇", "🥈", "🥉", "④"]
    recommended = []
    for i, (eid, sc) in enumerate(recs):
        recommended.append({
            "rank": i + 1,
            "medal": medals[i],
            "event_name": events[eid].name if eid in events else "未知",
            "score": sc.earned_score
        })

    return {
        "current_scores": current,
        "total": total,
        "max_total": len(events) * 10,
        "recommended": recommended,
        "history_by_date": dict(by_date)
    }

@router.put("/password")
def change_password(data: StudentPasswordChange, student_id: str = "", token: str = "", db: Session = Depends(get_db)):
    expected_token = f"student_"
    if not token.startswith(expected_token):
        raise HTTPException(401, "无效的登录凭证")
    db_id = int(token.split("_")[1])
    student = db.query(Student).get(db_id)
    if not student or student.student_id != student_id:
        raise HTTPException(401, "无效的登录凭证")

    if not verify_student_password(data.old_password, student.password_hash):
        raise HTTPException(400, "原密码错误")

    student.password_hash = hash_password(data.new_password)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Register router in main.py**

Add to `backend/app/main.py`:
```python
from .routers import student_portal as student_portal_router
app.include_router(student_portal_router.router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/student_portal.py backend/app/main.py
git commit -m "feat: student portal - login, scores, password change"
```

---

### Task 12: Seed Data

**Files:**
- Create: `backend/app/seed.py`

- [ ] **Step 1: Create seed script**

Create `backend/app/seed.py`:
```python
"""Seed default data: admin account, sport events with scoring standards, config."""
from .database import SessionLocal
from .models import Admin, SportEvent, ScoringStandard, SystemConfig, Gender, InputFormat
from .auth import hash_password

# Complete scoring standards from the user's tables
FEMALE_STANDARDS = {
    "800米跑": ["3'25", "3'35", "3'45", "3'55", "4'05", "4'15", "4'25", "4'35", "4'45", "4'55"],
    "足球运球": ["10.1", "11.0", "11.9", "12.9", "14.4", "15.4", "16.8", "17.7", "18.6", "19.7"],
    "50米跑": ["8.1", "8.3", "8.5", "8.7", "8.9", "9.1", "9.5", "9.9", "10.5", "10.9"],
    "立定跳远": ["1.97", "1.89", "1.81", "1.73", "1.65", "1.57", "1.49", "1.41", "1.33", "1.21"],
    "一分钟跳绳": ["170", "160", "150", "140", "130", "120", "110", "100", "90", "80"],
    "掷实心球": ["6.70", "6.30", "5.90", "5.50", "5.10", "4.70", "4.30", "3.90", "3.50", "3.10"],
    "篮球运球投篮": ["26", "32", "40", "46", "51", "56", "61", "66", "70", "85"],
    "一分钟仰卧起坐": ["50", "46", "42", "38", "34", "30", "26", "22", "18", "14"],
    "游泳": ["100", "90", "80", "70", "60", "50", "40", "30", "25", "1"],
}

MALE_STANDARDS = {
    "1000米跑": ["3'40", "3'50", "4'00", "4'10", "4'20", "4'30", "4'40", "4'50", "5'00", "5'10"],
    "足球运球": ["9.1", "10.0", "10.7", "11.5", "12.8", "13.6", "14.6", "15.2", "15.9", "16.8"],
    "50米跑": ["7.1", "7.3", "7.5", "7.7", "7.9", "8.1", "8.3", "8.7", "9.3", "9.7"],
    "立定跳远": ["2.46", "2.38", "2.30", "2.22", "2.14", "2.06", "1.98", "1.90", "1.82", "1.70"],
    "一分钟跳绳": ["180", "170", "160", "150", "140", "130", "120", "110", "100", "90"],
    "掷实心球": ["9.80", "9.20", "8.60", "8.00", "7.40", "6.80", "6.20", "5.60", "5.00", "4.40"],
    "篮球运球投篮": ["20", "24", "32", "38", "43", "48", "53", "57", "61", "69"],
    "引体向上": ["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"],
    "游泳": ["100", "90", "80", "70", "60", "50", "40", "30", "25", "1"],
}

EVENT_META = {
    "800米跑": {"gender": Gender.F, "higher_better": False, "unit": "分'秒", "input_format": InputFormat.time_ms, "sort_order": 1},
    "1000米跑": {"gender": Gender.M, "higher_better": False, "unit": "分'秒", "input_format": InputFormat.time_ms, "sort_order": 1},
    "足球运球": {"gender": Gender.both, "higher_better": False, "unit": "秒", "input_format": InputFormat.decimal_seconds, "sort_order": 2},
    "50米跑": {"gender": Gender.both, "higher_better": False, "unit": "秒", "input_format": InputFormat.decimal_seconds, "sort_order": 3},
    "立定跳远": {"gender": Gender.both, "higher_better": True, "unit": "米", "input_format": InputFormat.decimal_meters, "sort_order": 4},
    "一分钟跳绳": {"gender": Gender.both, "higher_better": True, "unit": "次", "input_format": InputFormat.integer, "sort_order": 5},
    "掷实心球": {"gender": Gender.both, "higher_better": True, "unit": "米", "input_format": InputFormat.decimal_meters, "sort_order": 6},
    "篮球运球投篮": {"gender": Gender.both, "higher_better": False, "unit": "秒", "input_format": InputFormat.decimal_seconds, "sort_order": 7},
    "一分钟仰卧起坐": {"gender": Gender.F, "higher_better": True, "unit": "次", "input_format": InputFormat.integer, "sort_order": 8},
    "引体向上": {"gender": Gender.M, "higher_better": True, "unit": "个", "input_format": InputFormat.integer, "sort_order": 8},
    "游泳": {"gender": Gender.both, "higher_better": True, "unit": "米", "input_format": InputFormat.integer, "sort_order": 9},
}

def seed():
    db = SessionLocal()

    # Skip if already seeded
    if db.query(Admin).first():
        print("Already seeded, skipping.")
        db.close()
        return

    # Default admin
    admin = Admin(
        username="admin",
        password_hash=hash_password("admin123"),
        is_super=True,
        display_name="超级管理员"
    )
    db.add(admin)

    # Sport events with standards
    for name, meta in EVENT_META.items():
        event = SportEvent(
            name=name,
            gender=meta["gender"],
            higher_better=meta["higher_better"],
            unit=meta["unit"],
            input_format=meta["input_format"],
            sort_order=meta["sort_order"]
        )
        db.add(event)
        db.flush()

        # Female standards
        if name in FEMALE_STANDARDS:
            for i, val in enumerate(FEMALE_STANDARDS[name]):
                db.add(ScoringStandard(event_id=event.id, score=10 - i, standard_value=val))
        # Male standards
        if name in MALE_STANDARDS:
            for i, val in enumerate(MALE_STANDARDS[name]):
                db.add(ScoringStandard(event_id=event.id, score=10 - i, standard_value=val))

    # System config
    configs = [
        SystemConfig(key="school_name", value="江东中心学校体育成绩管理中心"),
        SystemConfig(key="praise_threshold", value="1"),
        SystemConfig(key="warning_threshold", value="2"),
        SystemConfig(key="designer", value="tequila"),
    ]
    for c in configs:
        db.add(c)

    db.commit()
    db.close()
    print("Seed data created successfully.")

if __name__ == "__main__":
    seed()
```

- [ ] **Step 2: Run seed**

Run: `cd backend; python -m app.seed`
Expected: "Seed data created successfully."

- [ ] **Step 3: Commit**

```bash
git add backend/app/seed.py
git commit -m "feat: seed data with 11 sports, full scoring standards, default admin"
```

---

### Task 13: Frontend Routing & API Layer

**Files:**
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/api/index.js`

- [ ] **Step 1: Create API layer**

Create `frontend/src/api/index.js`:
```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// Request interceptor: attach admin token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_info')
      if (window.location.pathname.startsWith('/admin') && !window.location.pathname.includes('/admin/login')) {
        window.location.href = '/admin/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
```

- [ ] **Step 2: Create router**

Create `frontend/src/router/index.js`:
```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../views/admin/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/admin',
    component: () => import('../views/admin/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/admin/Dashboard.vue') },
      { path: 'score-entry', name: 'ScoreEntry', component: () => import('../views/admin/ScoreEntry.vue') },
      { path: 'students', name: 'Students', component: () => import('../views/admin/Students.vue') },
      { path: 'statistics', name: 'Statistics', component: () => import('../views/admin/Statistics.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/admin/Settings.vue') }
    ]
  },
  {
    path: '/student/login',
    name: 'StudentLogin',
    component: () => import('../views/student/Login.vue')
  },
  {
    path: '/student/scores',
    name: 'StudentScores',
    component: () => import('../views/student/Scores.vue')
  },
  { path: '/', redirect: '/admin/login' },
  { path: '/:pathMatch(.*)*', redirect: '/admin/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('admin_token')
    if (!token) {
      return next('/admin/login')
    }
  }
  next()
})

export default router
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.js frontend/src/api/index.js
git commit -m "feat: Vue Router and Axios API layer"
```

---

### Task 14: Admin Login Page

**Files:**
- Create: `frontend/src/views/admin/Login.vue`

- [ ] **Step 1: Create admin login page**

Create `frontend/src/views/admin/Login.vue`:
```vue
<template>
  <div class="login-container">
    <div class="login-card">
      <h1>{{ schoolName }}</h1>
      <h2>管理员登录</h2>
      <el-form @submit.prevent="login">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" @click="login" :loading="loading" style="width:100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <p class="designer">Designed by {{ designer }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const schoolName = ref('体育成绩管理系统')
const designer = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/config/public')
    schoolName.value = res.data.school_name || schoolName.value
    designer.value = res.data.designer || ''
  } catch {}
})

async function login() {
  loading.value = true
  try {
    const res = await api.post('/auth/login', {
      username: username.value,
      password: password.value
    })
    localStorage.setItem('admin_token', res.data.access_token)
    localStorage.setItem('admin_info', JSON.stringify(res.data.admin))
    router.push('/admin/dashboard')
  } catch {
    ElMessage.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  background: white; padding: 40px; border-radius: 12px;
  width: 400px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.login-card h1 { text-align: center; font-size: 20px; color: #333; margin-bottom: 4px; }
.login-card h2 { text-align: center; font-size: 16px; color: #999; margin-bottom: 24px; font-weight: normal; }
.designer { text-align: center; color: #ccc; font-size: 12px; margin-top: 16px; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/admin/Login.vue
git commit -m "feat: admin login page with dynamic school name"
```

---

### Task 15: Admin Layout

**Files:**
- Create: `frontend/src/views/admin/Layout.vue`
- Create: `frontend/src/views/admin/Dashboard.vue`

- [ ] **Step 1: Create Layout with sidebar**

Create `frontend/src/views/admin/Layout.vue`:
```vue
<template>
  <el-container style="min-height:100vh">
    <el-aside width="220px" style="background:#304156">
      <div class="logo">{{ schoolName }}</div>
      <el-menu :default-active="route.path" background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF" router>
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon> 仪表盘
        </el-menu-item>
        <el-menu-item index="/admin/score-entry">
          <el-icon><EditPen /></el-icon> 成绩录入
        </el-menu-item>
        <el-menu-item index="/admin/students">
          <el-icon><User /></el-icon> 学生管理
        </el-menu-item>
        <el-menu-item index="/admin/statistics">
          <el-icon><TrendCharts /></el-icon> 统计分析
        </el-menu-item>
        <el-menu-item v-if="adminInfo?.is_super" index="/admin/settings">
          <el-icon><Setting /></el-icon> 开发人员选项
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background:white;border-bottom:1px solid #eee;display:flex;align-items:center;justify-content:flex-end">
        <span>{{ adminInfo?.display_name }}</span>
        <el-button type="danger" text @click="logout" style="margin-left:16px">退出</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../api'

const router = useRouter()
const route = useRoute()
const adminInfo = ref(null)
const schoolName = ref('')

onMounted(async () => {
  const info = localStorage.getItem('admin_info')
  if (info) adminInfo.value = JSON.parse(info)
  try {
    const res = await api.get('/config/public')
    schoolName.value = res.data.school_name || '体育成绩管理系统'
  } catch {}
})

function logout() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_info')
  router.push('/admin/login')
}
</script>

<style scoped>
.logo {
  color: white; text-align: center; padding: 16px 8px;
  font-size: 15px; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.1);
  word-break: break-all;
}
</style>
```

- [ ] **Step 2: Create Dashboard placeholder**

Create `frontend/src/views/admin/Dashboard.vue`:
```vue
<template>
  <div>
    <h3>欢迎使用体育成绩管理系统</h3>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>快捷入口</template>
          <el-button type="primary" @click="$router.push('/admin/score-entry')">成绩录入</el-button>
          <el-button @click="$router.push('/admin/students')">学生管理</el-button>
          <el-button @click="$router.push('/admin/statistics')">统计分析</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/admin/Layout.vue frontend/src/views/admin/Dashboard.vue
git commit -m "feat: admin layout with sidebar navigation and dashboard"
```

---

### Task 16: Score Entry Page (Core)

**Files:**
- Create: `frontend/src/views/admin/ScoreEntry.vue`
- Create: `frontend/src/components/VoiceButton.vue`

- [ ] **Step 1: Create VoiceButton component**

Create `frontend/src/components/VoiceButton.vue`:
```vue
<template>
  <el-button
    :type="recording ? 'danger' : 'default'"
    circle
    size="large"
    @click="startRecording"
    :loading="processing"
  >
    {{ recording ? '⏹' : '🎤' }}
  </el-button>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['result'])
const recording = ref(false)
const processing = ref(false)

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
const recognition = SpeechRecognition ? new SpeechRecognition() : null

if (recognition) {
  recognition.lang = 'zh-CN'
  recognition.interimResults = false
  recognition.maxAlternatives = 1

  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript
    // Convert Chinese numbers to digits: "八点一" -> "8.1"
    const result = convertChineseNumbers(text)
    emit('result', result)
    processing.value = false
  }

  recognition.onerror = () => {
    ElMessage.warning('语音识别失败，请重试')
    recording.value = false
    processing.value = false
  }

  recognition.onend = () => {
    recording.value = false
  }
}

function startRecording() {
  if (!recognition) {
    ElMessage.warning('您的浏览器不支持语音识别，请使用Chrome浏览器')
    return
  }
  recording.value = true
  processing.value = true
  recognition.start()
  // Auto-stop after 1.5 seconds
  setTimeout(() => {
    if (recording.value) {
      recognition.stop()
    }
  }, 1500)
}

function convertChineseNumbers(text) {
  const map = {
    '零': '0', '一': '1', '二': '2', '三': '3', '四': '4',
    '五': '5', '六': '6', '七': '7', '八': '8', '九': '9',
    '十': '10', '点': '.', '秒': '', '分': "'", '米': '', '个': '', '次': ''
  }
  let result = text
  for (const [cn, num] of Object.entries(map)) {
    result = result.replace(new RegExp(cn, 'g'), num)
  }
  return result.replace(/[^0-9.'\-]/g, '')
}
</script>
```

- [ ] **Step 2: Create ScoreEntry page**

Create `frontend/src/views/admin/ScoreEntry.vue`:
```vue
<template>
  <div class="score-entry">
    <!-- Step 1: Select class, event, date -->
    <div v-if="!started">
      <h3>成绩录入</h3>
      <el-form label-width="80px" style="max-width:400px">
        <el-form-item label="选择班级">
          <el-select v-model="selectedClassId" placeholder="请选择班级" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择项目">
          <el-select v-model="selectedEventId" placeholder="请选择项目" style="width:100%">
            <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试日期">
          <el-date-picker v-model="testDate" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startEntry" :disabled="!selectedClassId || !selectedEventId">
            开始录入
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Step 2: Per-student entry -->
    <div v-else>
      <div class="entry-header">
        <el-button text @click="started = false">← 返回</el-button>
        <span>{{ selectedClass?.label }} - {{ selectedEvent?.name }}</span>
      </div>

      <div class="student-card" v-if="currentStudent">
        <div class="student-nav">
          <el-button circle @click="prevStudent" :disabled="currentIndex === 0">◀</el-button>
          <div class="student-info">
            <div class="student-name">{{ currentStudent.name }}</div>
            <div class="student-id">{{ currentStudent.student_id }}</div>
            <div class="progress">{{ currentIndex + 1 }} / {{ students.length }}</div>
          </div>
          <el-button circle @click="nextStudent" :disabled="currentIndex >= students.length - 1">▶</el-button>
        </div>

        <div class="input-area">
          <el-input
            v-model="currentValue"
            :placeholder="getPlaceholder()"
            size="large"
            class="score-input"
            @input="onValueChange"
          />
        </div>

        <div class="voice-area">
          <VoiceButton @result="onVoiceResult" />
        </div>

        <div class="score-result" v-if="currentScore !== null">
          <div class="earned">得分: {{ currentScore }} 分</div>
          <div class="change" v-if="previousScore !== null">
            上次: {{ previousScore }} 分
            <span v-if="change > 0 && isPraise" class="praise">↑+{{ change }} ✨ 进步表扬</span>
            <span v-else-if="change < 0 && isWarning" class="warning">↓{{ change }} 🟠 橙色预警</span>
            <span v-else-if="change > 0">↑+{{ change }}</span>
            <span v-else-if="change < 0">↓{{ change }}</span>
            <span v-else>→ 持平</span>
          </div>
          <div v-else class="change muted">- 首次测试</div>
        </div>

        <el-button type="primary" size="large" @click="saveAndNext" :loading="saving" class="save-btn">
          保存并下一个
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'
import VoiceButton from '../../components/VoiceButton.vue'

const classes = ref([])
const events = ref([])
const selectedClassId = ref(null)
const selectedEventId = ref(null)
const testDate = ref(new Date().toISOString().split('T')[0])
const started = ref(false)

const students = ref([])
const currentIndex = ref(0)
const currentValue = ref('')
const currentScore = ref(null)
const previousScore = ref(null)
const change = ref(null)
const isPraise = ref(false)
const isWarning = ref(false)
const saving = ref(false)

const selectedClass = computed(() => classes.value.find(c => c.id === selectedClassId.value))
const selectedEvent = computed(() => events.value.find(e => e.id === selectedEventId.value))
const currentStudent = computed(() => students.value[currentIndex.value])

onMounted(async () => {
  const [cRes, eRes] = await Promise.all([
    api.get('/events/classes'),
    api.get('/events')
  ])
  classes.value = cRes.data
  events.value = eRes.data
})

function getPlaceholder() {
  if (!selectedEvent.value) return '输入成绩'
  const fmt = selectedEvent.value.input_format
  if (fmt === 'time_ms') return "例如: 3'30"
  if (fmt === 'decimal_seconds') return '例如: 8.1'
  if (fmt === 'decimal_meters') return '例如: 1.95'
  return '例如: 170'
}

async function startEntry() {
  const res = await api.get(`/scores/student-list/${selectedClassId.value}`)
  students.value = res.data
  currentIndex.value = 0
  currentValue.value = ''
  currentScore.value = null
  previousScore.value = null
  change.value = null
  started.value = true
}

function prevStudent() { if (currentIndex.value > 0) { currentIndex.value--; resetInput() } }
function nextStudent() { if (currentIndex.value < students.value.length - 1) { currentIndex.value++; resetInput() } }

function resetInput() {
  currentValue.value = ''
  currentScore.value = null
  previousScore.value = null
  change.value = null
  isPraise.value = false
  isWarning.value = false
}

function onVoiceResult(text) {
  currentValue.value = text
  onValueChange()
}

async function onValueChange() {
  if (!currentValue.value) { currentScore.value = null; return }
  try {
    const res = await api.post('/scores/batch', {
      scores: [{
        student_id: currentStudent.value.id,
        event_id: selectedEventId.value,
        raw_value: currentValue.value,
        test_date: testDate.value
      }]
    })
    const result = res.data[0]
    currentScore.value = result.earned_score
    previousScore.value = result.previous_score
    change.value = result.change
    isPraise.value = result.is_praise
    isWarning.value = result.is_warning
  } catch {
    currentScore.value = null
  }
}

async function saveAndNext() {
  if (!currentValue.value) { ElMessage.warning('请先输入成绩'); return }
  saving.value = true
  try {
    await api.post('/scores/batch', {
      scores: [{
        student_id: currentStudent.value.id,
        event_id: selectedEventId.value,
        raw_value: currentValue.value,
        test_date: testDate.value
      }]
    })
    ElMessage.success('保存成功')
    if (currentIndex.value < students.value.length - 1) {
      nextStudent()
    } else {
      ElMessage.success('全部录入完成！')
    }
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.student-card { max-width: 400px; margin: 20px auto; text-align: center; }
.student-nav { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.student-info { flex: 1; }
.student-name { font-size: 22px; font-weight: bold; }
.student-id { color: #999; font-size: 14px; }
.progress { color: #ccc; font-size: 12px; margin-top: 4px; }
.input-area { margin: 20px 0; }
.score-input :deep(.el-input__inner) { text-align: center; font-size: 24px; }
.voice-area { margin: 16px 0; }
.score-result { margin: 20px 0; padding: 16px; background: #f5f7fa; border-radius: 8px; }
.earned { font-size: 28px; font-weight: bold; color: #409EFF; }
.change { font-size: 14px; margin-top: 8px; }
.praise { color: #67c23a; font-weight: bold; }
.warning { color: #e6a23c; font-weight: bold; }
.muted { color: #ccc; }
.save-btn { width: 100%; margin-top: 16px; }
.entry-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; font-size: 16px; font-weight: bold; }
</style>
```

- [ ] **Step 3: Verify the page loads**

Run: `cd frontend; npm run dev`
Manual: Navigate to http://localhost:5173/admin/login, login with admin/admin123, then go to 成绩录入. Verify class/event selection and per-student entry interface renders.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/admin/ScoreEntry.vue frontend/src/components/VoiceButton.vue
git commit -m "feat: score entry page with voice input and real-time scoring"
```

---

### Task 17: Student Management Page

**Files:**
- Create: `frontend/src/views/admin/Students.vue`

- [ ] **Step 1: Create Students page**

Create `frontend/src/views/admin/Students.vue`:
```vue
<template>
  <div>
    <h3>学生管理</h3>

    <el-row :gutter="10" style="margin-bottom:16px">
      <el-col :span="6">
        <el-input v-model="search" placeholder="搜索学号/姓名" clearable @change="loadStudents" />
      </el-col>
      <el-col :span="6">
        <el-select v-model="filterClassId" placeholder="筛选班级" clearable @change="loadStudents" style="width:100%">
          <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
        </el-select>
      </el-col>
      <el-col :span="12" style="text-align:right">
        <el-button @click="downloadTemplate">下载导入模板</el-button>
        <el-button type="primary" @click="showImport = true">批量导入</el-button>
        <el-button @click="showBatchEdit = true">批量修改</el-button>
      </el-col>
    </el-row>

    <el-table :data="students" border stripe style="width:100%">
      <el-table-column prop="student_id" label="学号" width="120" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column label="性别" width="60">
        <template #default="{ row }">{{ row.gender === 'M' ? '男' : '女' }}</template>
      </el-table-column>
      <el-table-column label="班级">
        <template #default="{ row }">{{ row.class_grade }}{{ row.class_name }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button text type="primary" @click="editStudent(row)">编辑</el-button>
          <el-button text type="danger" @click="deleteStudent(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="50"
      :total="total"
      layout="prev, pager, next, total"
      @current-change="loadStudents"
      style="margin-top:16px;justify-content:center"
    />

    <!-- Import dialog -->
    <el-dialog v-model="showImport" title="批量导入学生" width="500px">
      <el-upload
        :http-request="handleImport"
        accept=".xlsx"
        :show-file-list="false"
        drag
      >
        <div>拖拽Excel文件到此处或点击上传</div>
      </el-upload>
      <div v-if="importResult" style="margin-top:16px">
        <p>导入成功: {{ importResult.imported }} 人</p>
        <p v-for="e in importResult.errors" :key="e" style="color:red;font-size:12px">{{ e }}</p>
      </div>
    </el-dialog>

    <!-- Batch edit dialog -->
    <el-dialog v-model="showBatchEdit" title="批量修改" width="400px">
      <el-form label-width="80px">
        <el-form-item label="原班级">
          <el-select v-model="batchFromClass" placeholder="留空=全部" clearable style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="新班级">
          <el-select v-model="batchToClass" placeholder="选择目标班级" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="batchResetPwd">重置密码（学号后6位）</el-checkbox>
        </el-form-item>
        <el-button type="primary" @click="doBatchUpdate">确认修改</el-button>
      </el-form>
    </el-dialog>

    <!-- Edit student dialog -->
    <el-dialog v-model="showEdit" title="编辑学生" width="400px">
      <el-form label-width="80px" v-if="editForm">
        <el-form-item label="学号"><el-input v-model="editForm.student_id" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="editForm.name" /></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="editForm.gender">
            <el-option label="男" value="M" /><el-option label="女" value="F" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="editForm.class_id" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const students = ref([])
const classes = ref([])
const search = ref('')
const filterClassId = ref(null)
const page = ref(1)
const total = ref(0)

const showImport = ref(false)
const showBatchEdit = ref(false)
const showEdit = ref(false)
const importResult = ref(null)
const batchFromClass = ref(null)
const batchToClass = ref(null)
const batchResetPwd = ref(false)
const editForm = ref(null)

onMounted(async () => {
  const res = await api.get('/events/classes')
  classes.value = res.data
  loadStudents()
})

async function loadStudents() {
  const params = { page: page.value, page_size: 50 }
  if (search.value) params.search = search.value
  if (filterClassId.value) params.class_id = filterClassId.value
  const res = await api.get('/students', { params })
  students.value = res.data
}

function downloadTemplate() {
  window.open('/api/students/template/download')
}

async function handleImport({ file }) {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post('/students/batch-import', form)
  importResult.value = res.data
  loadStudents()
}

async function doBatchUpdate() {
  await api.put('/students/batch/update', {
    class_id: batchFromClass.value,
    new_class_id: batchToClass.value || undefined,
    reset_password: batchResetPwd.value
  })
  ElMessage.success('批量修改成功')
  showBatchEdit.value = false
  loadStudents()
}

function editStudent(row) {
  editForm.value = { ...row }
  showEdit.value = true
}

async function saveEdit() {
  await api.put(`/students/${editForm.value.id}`, {
    student_id: editForm.value.student_id,
    name: editForm.value.name,
    gender: editForm.value.gender,
    class_id: editForm.value.class_id
  })
  ElMessage.success('修改成功')
  showEdit.value = false
  loadStudents()
}

async function deleteStudent(row) {
  await ElMessageBox.confirm(`确定删除 ${row.name} (${row.student_id})？`, '确认删除', { type: 'warning' })
  await api.delete(`/students/${row.id}`)
  ElMessage.success('删除成功')
  loadStudents()
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/admin/Students.vue
git commit -m "feat: student management page with import/export/batch edit"
```

---

### Task 18: Statistics Page

**Files:**
- Create: `frontend/src/views/admin/Statistics.vue`

- [ ] **Step 1: Create Statistics page**

Create `frontend/src/views/admin/Statistics.vue`:
```vue
<template>
  <div>
    <h3>统计分析</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="班级统计" name="class">
        <el-row :gutter="10" style="margin-bottom:16px">
          <el-col :span="8">
            <el-select v-model="statsClassId" placeholder="选择班级" @change="loadClassStats" style="width:100%">
              <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
            </el-select>
          </el-col>
          <el-col :span="16">
            <el-select v-model="statsEventIds" multiple placeholder="选择项目（默认全部）" @change="loadClassStats" style="width:100%">
              <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
            </el-select>
          </el-col>
        </el-row>
        <el-button type="primary" @click="exportClassScores" style="margin-bottom:16px">导出班级成绩</el-button>

        <el-row :gutter="20" v-if="classStats">
          <el-col :span="6">
            <el-card><template #header>平均分</template><h2>{{ classStats.avg_score }}</h2></el-card>
          </el-col>
          <el-col :span="6">
            <el-card><template #header>优秀率(9-10分)</template><h2>{{ classStats.excellent_rate }}%</h2></el-card>
          </el-col>
          <el-col :span="6">
            <el-card><template #header>及格率(≥6分)</template><h2>{{ classStats.pass_rate }}%</h2></el-card>
          </el-col>
          <el-col :span="6">
            <el-card><template #header>总人数</template><h2>{{ classStats.total_students }}</h2></el-card>
          </el-col>
        </el-row>

        <div v-if="classStats?.event_avgs?.length" style="margin-top:20px">
          <h4>各项目平均分</h4>
          <div v-for="e in classStats.event_avgs" :key="e.event_id" class="event-bar">
            <span class="event-name">{{ e.event_name }}</span>
            <el-progress :percentage="e.avg_score * 10" :color="'#409EFF'" style="flex:1;margin:0 12px" />
            <span>{{ e.avg_score }}</span>
          </div>
        </div>

        <div v-if="classStats?.warning_students?.length" style="margin-top:20px">
          <h4 style="color:#e6a23c">退步预警学生</h4>
          <el-table :data="classStats.warning_students" border size="small">
            <el-table-column prop="student_no" label="学号" />
            <el-table-column prop="student_name" label="姓名" />
            <el-table-column prop="event_name" label="项目" />
            <el-table-column prop="prev_score" label="上次" />
            <el-table-column prop="curr_score" label="本次" />
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="个人统计" name="student">
        <el-row :gutter="10" style="margin-bottom:16px">
          <el-col :span="8">
            <el-input v-model="studentSearch" placeholder="输入学号或姓名搜索学生" @change="searchStudent" />
          </el-col>
          <el-col :span="16">
            <el-select v-model="studentEventIds" multiple placeholder="选择项目（默认全部）" @change="loadStudentStats" style="width:100%">
              <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
            </el-select>
          </el-col>
        </el-row>

        <div v-if="studentStats">
          <h4>{{ studentStats.student.name }} ({{ studentStats.student.student_id }})</h4>
          <el-button @click="exportStudentScores" style="margin-bottom:16px">导出个人成绩</el-button>

          <el-card style="margin-bottom:16px">
            <template #header>中考推荐项目</template>
            <div v-for="r in studentStats.recommended_events" :key="r.rank" style="margin:8px 0;font-size:18px">
              {{ r.medal }} {{ r.event_name }} — {{ r.score }} 分
            </div>
          </el-card>

          <el-card v-if="studentStats.scores_by_event">
            <template #header>各项目得分</template>
            <div v-for="(scores, eventName) in studentStats.scores_by_event" :key="eventName" style="margin:8px 0">
              <strong>{{ eventName }}</strong>:
              <span v-for="sc in scores" :key="sc.id" style="margin-left:8px">
                {{ sc.earned_score }}({{ sc.test_date }})
              </span>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const activeTab = ref('class')
const classes = ref([])
const events = ref([])

// Class stats
const statsClassId = ref(null)
const statsEventIds = ref([])
const classStats = ref(null)

// Student stats
const studentSearch = ref('')
const studentEventIds = ref([])
const studentStats = ref(null)

onMounted(async () => {
  const [cRes, eRes] = await Promise.all([
    api.get('/events/classes'),
    api.get('/events')
  ])
  classes.value = cRes.data
  events.value = eRes.data
})

async function loadClassStats() {
  if (!statsClassId.value) return
  const params = { class_id: statsClassId.value }
  if (statsEventIds.value.length) params.event_ids = statsEventIds.value.join(',')
  const res = await api.get('/scores/class-stats', { params })
  classStats.value = res.data
}

async function searchStudent() {
  const res = await api.get('/students', { params: { search: studentSearch.value, page_size: 10 } })
  if (res.data.length > 0) {
    loadStudentStats(res.data[0].id)
  }
}

async function loadStudentStats(studentId) {
  const params = {}
  if (studentEventIds.value.length) params.event_ids = studentEventIds.value.join(',')
  const res = await api.get(`/scores/student-stats/${studentId}`, { params })
  studentStats.value = res.data
}

function exportClassScores() {
  if (!statsClassId.value) return
  let url = `/api/scores/export/class?class_id=${statsClassId.value}`
  if (statsEventIds.value.length) url += `&event_ids=${statsEventIds.value.join(',')}`
  window.open(url)
}

function exportStudentScores() {
  if (!studentStats.value) return
  window.open(`/api/scores/export/student/${studentStats.value.student.id}`)
}
</script>

<style scoped>
.event-bar { display: flex; align-items: center; margin: 8px 0; }
.event-name { width: 120px; font-size: 14px; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/admin/Statistics.vue
git commit -m "feat: statistics page with class/personal stats and export"
```

---

### Task 19: Settings Page (Super Admin)

**Files:**
- Create: `frontend/src/views/admin/Settings.vue`

- [ ] **Step 1: Create Settings page**

Create `frontend/src/views/admin/Settings.vue`:
```vue
<template>
  <div>
    <h3>开发人员选项</h3>

    <el-tabs>
      <!-- Sport Events -->
      <el-tab-pane label="运动项目设置">
        <el-table :data="events" border>
          <el-table-column prop="name" label="项目名称" />
          <el-table-column label="性别">
            <template #default="{ row }">{{ row.gender === 'M' ? '男' : row.gender === 'F' ? '女' : '通用' }}</template>
          </el-table-column>
          <el-table-column label="方向">
            <template #default="{ row }">{{ row.higher_better ? '越大越好' : '越小越好' }}</template>
          </el-table-column>
          <el-table-column prop="unit" label="单位" />
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button text type="primary" @click="editStandards(row)">编辑标准</el-button>
              <el-button text type="danger" @click="deleteEvent(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button @click="showAddEvent = true" style="margin-top:16px">新增项目</el-button>

        <el-dialog v-model="showAddEvent" title="新增项目" width="400px">
          <el-form label-width="80px">
            <el-form-item label="名称"><el-input v-model="newEvent.name" /></el-form-item>
            <el-form-item label="性别">
              <el-select v-model="newEvent.gender">
                <el-option label="通用" value="both" /><el-option label="男" value="M" /><el-option label="女" value="F" />
              </el-select>
            </el-form-item>
            <el-form-item label="方向">
              <el-select v-model="newEvent.higher_better">
                <el-option label="越大越好" :value="true" /><el-option label="越小越好" :value="false" />
              </el-select>
            </el-form-item>
            <el-form-item label="单位"><el-input v-model="newEvent.unit" /></el-form-item>
            <el-form-item label="格式">
              <el-select v-model="newEvent.input_format">
                <el-option label="分'秒" value="time_ms" />
                <el-option label="十进制秒" value="decimal_seconds" />
                <el-option label="十进制米" value="decimal_meters" />
                <el-option label="整数" value="integer" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="addEvent">确认新增</el-button>
          </el-form>
        </el-dialog>

        <el-dialog v-model="showStandards" title="编辑评分标准" width="500px">
          <el-form v-for="i in 10" :key="i" label-width="60px" :inline="true">
            <el-form-item :label="`${11 - i}分`">
              <el-input v-model="standardsForm[i - 1]" style="width:200px" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="saveStandards">保存</el-button>
        </el-dialog>
      </el-tab-pane>

      <!-- Admins -->
      <el-tab-pane label="管理员管理">
        <el-table :data="admins" border>
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="display_name" label="姓名" />
          <el-table-column label="角色">
            <template #default="{ row }">{{ row.is_super ? '超管' : '老师' }}</template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button text type="danger" @click="deleteAdmin(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button @click="showAddAdmin = true" style="margin-top:16px">新增管理员</el-button>
        <el-dialog v-model="showAddAdmin" title="新增管理员" width="400px">
          <el-form label-width="80px">
            <el-form-item label="用户名"><el-input v-model="newAdmin.username" /></el-form-item>
            <el-form-item label="密码"><el-input v-model="newAdmin.password" type="password" /></el-form-item>
            <el-form-item label="姓名"><el-input v-model="newAdmin.display_name" /></el-form-item>
            <el-form-item label="角色">
              <el-select v-model="newAdmin.is_super">
                <el-option label="老师" :value="false" /><el-option label="超管" :value="true" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="addAdmin">确认新增</el-button>
          </el-form>
        </el-dialog>
      </el-tab-pane>

      <!-- System Config -->
      <el-tab-pane label="系统设置">
        <el-form label-width="100px" style="max-width:500px">
          <el-form-item label="学校名称">
            <el-input v-model="config.school_name" />
          </el-form-item>
          <el-form-item label="进步表扬阈值">
            <el-input-number v-model="config.praise_threshold" :min="1" :max="10" />
            <span style="margin-left:8px;color:#999">分值提升≥此值即表扬</span>
          </el-form-item>
          <el-form-item label="橙色预警阈值">
            <el-input-number v-model="config.warning_threshold" :min="1" :max="10" />
            <span style="margin-left:8px;color:#999">分值下降≥此值即预警</span>
          </el-form-item>
          <el-form-item label="设计者">
            <el-input v-model="config.designer" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveConfig">保存设置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const events = ref([])
const admins = ref([])
const config = ref({ school_name: '', praise_threshold: 1, warning_threshold: 2, designer: '' })

// Events
const showAddEvent = ref(false)
const newEvent = ref({ name: '', gender: 'both', higher_better: true, unit: '', input_format: 'decimal_seconds' })
const showStandards = ref(false)
const editingEventId = ref(null)
const standardsForm = ref(Array(10).fill(''))

onMounted(async () => {
  const [eRes, aRes, cRes] = await Promise.all([
    api.get('/events'),
    api.get('/admins'),
    api.get('/config')
  ])
  events.value = eRes.data
  admins.value = aRes.data
  for (const c of cRes.data) {
    if (c.key in config.value) config.value[c.key] = c.key.includes('threshold') ? parseInt(c.value) : c.value
  }
})

async function addEvent() {
  await api.post('/events', newEvent.value)
  ElMessage.success('项目已新增')
  showAddEvent.value = false
  newEvent.value = { name: '', gender: 'both', higher_better: true, unit: '', input_format: 'decimal_seconds' }
  const res = await api.get('/events')
  events.value = res.data
}

async function deleteEvent(row) {
  await ElMessageBox.confirm(`确定删除 ${row.name}？`)
  await api.delete(`/events/${row.id}`)
  const res = await api.get('/events')
  events.value = res.data
}

function editStandards(row) {
  editingEventId.value = row.id
  // Load existing standards, sort by score desc (10->1)
  const stds = [...row.standards].sort((a, b) => b.score - a.score)
  standardsForm.value = stds.map(s => s.standard_value)
  showStandards.value = true
}

async function saveStandards() {
  const payload = []
  for (let i = 0; i < 10; i++) {
    if (standardsForm.value[i]) {
      payload.push({ score: 10 - i, standard_value: standardsForm.value[i] })
    }
  }
  await api.put(`/events/${editingEventId.value}/standards`, payload)
  ElMessage.success('标准已更新')
  showStandards.value = false
  const res = await api.get('/events')
  events.value = res.data
}

// Admins
const showAddAdmin = ref(false)
const newAdmin = ref({ username: '', password: '', display_name: '', is_super: false })

async function addAdmin() {
  await api.post('/admins', newAdmin.value)
  ElMessage.success('管理员已创建')
  showAddAdmin.value = false
  const res = await api.get('/admins')
  admins.value = res.data
}

async function deleteAdmin(row) {
  await ElMessageBox.confirm(`确定删除管理员 ${row.display_name}？`)
  await api.delete(`/admins/${row.id}`)
  const res = await api.get('/admins')
  admins.value = res.data
}

// Config
async function saveConfig() {
  for (const [key, value] of Object.entries(config.value)) {
    await api.put(`/config/${key}`, { value: String(value) })
  }
  ElMessage.success('配置已保存')
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/admin/Settings.vue
git commit -m "feat: super admin settings page with events, admins, config"
```

---

### Task 20: Student Portal (Login + Scores)

**Files:**
- Create: `frontend/src/views/student/Login.vue`
- Create: `frontend/src/views/student/Scores.vue`

- [ ] **Step 1: Create student login page**

Create `frontend/src/views/student/Login.vue`:
```vue
<template>
  <div class="login-container">
    <div class="login-card">
      <h1>{{ schoolName }}</h1>
      <h2>学生成绩查询</h2>
      <el-form @submit.prevent="login">
        <el-form-item>
          <el-input v-model="studentId" placeholder="学号" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" @click="login" :loading="loading" style="width:100%">登录</el-button>
        </el-form-item>
        <el-form-item>
          <el-button text @click="showChangePwd = true">修改密码</el-button>
        </el-form-item>
      </el-form>
      <p class="designer">Designed by {{ designer }}</p>
    </div>

    <el-dialog v-model="showChangePwd" title="修改密码" width="350px">
      <el-form label-width="80px">
        <el-form-item label="学号"><el-input v-model="studentId" /></el-form-item>
        <el-form-item label="原密码"><el-input v-model="oldPwd" type="password" /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="newPwd" type="password" /></el-form-item>
        <el-button type="primary" @click="changePassword">确认修改</el-button>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const studentId = ref('')
const password = ref('')
const loading = ref(false)
const schoolName = ref('体育成绩管理系统')
const designer = ref('')

const showChangePwd = ref(false)
const oldPwd = ref('')
const newPwd = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/config/public')
    schoolName.value = res.data.school_name || schoolName.value
    designer.value = res.data.designer || ''
  } catch {}
})

async function login() {
  loading.value = true
  try {
    const res = await api.post('/student/login', {
      student_id: studentId.value,
      password: password.value
    })
    sessionStorage.setItem('student_token', res.data.token)
    sessionStorage.setItem('student_id', studentId.value)
    sessionStorage.setItem('student_info', JSON.stringify(res.data.student))
    router.push('/student/scores')
  } catch {
    ElMessage.error('学号或密码错误')
  } finally { loading.value = false }
}

async function changePassword() {
  try {
    await api.put('/student/password', {
      old_password: oldPwd.value,
      new_password: newPwd.value
    }, {
      params: { student_id: studentId.value, token: sessionStorage.getItem('student_token') || '' }
    })
    ElMessage.success('密码修改成功')
    showChangePwd.value = false
  } catch { ElMessage.error('修改失败，请检查原密码') }
}
</script>

<style scoped>
.login-container {
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}
.login-card {
  background: white; padding: 40px; border-radius: 12px;
  width: 400px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.login-card h1 { text-align: center; font-size: 20px; color: #333; margin-bottom: 4px; }
.login-card h2 { text-align: center; font-size: 16px; color: #999; margin-bottom: 24px; font-weight: normal; }
.designer { text-align: center; color: #ccc; font-size: 12px; margin-top: 16px; }
</style>
```

- [ ] **Step 2: Create student scores page**

Create `frontend/src/views/student/Scores.vue`:
```vue
<template>
  <div style="max-width:600px;margin:0 auto;padding:20px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <h3>{{ schoolName }}</h3>
      <div>
        <span>{{ studentInfo?.name }}</span>
        <el-button text @click="showChangePwd = true">修改密码</el-button>
        <el-button text type="danger" @click="logout">退出</el-button>
      </div>
    </div>

    <h4>{{ studentInfo?.class_grade }}{{ studentInfo?.class_name }} | {{ studentInfo?.student_id }}</h4>

    <el-card style="margin-bottom:16px">
      <template #header>本学期成绩总览</template>
      <el-table :data="currentScores" border size="small">
        <el-table-column prop="event_name" label="项目" />
        <el-table-column prop="raw_value" label="成绩" />
        <el-table-column prop="earned_score" label="得分" />
      </el-table>
      <div style="text-align:right;margin-top:12px;font-size:18px;font-weight:bold">
        总分: {{ total }} / {{ maxTotal }}
      </div>
    </el-card>

    <el-card style="margin-bottom:16px">
      <template #header>中考推荐项目</template>
      <div v-for="r in recommended" :key="r.rank" style="font-size:18px;margin:8px 0">
        {{ r.medal }} {{ r.event_name }} — {{ r.score }} 分
      </div>
    </el-card>

    <el-card>
      <template #header>历史成绩记录</template>
      <div v-for="(scores, date) in history" :key="date" style="margin-bottom:16px">
        <strong>{{ date }}</strong>
        <div v-for="sc in scores" :key="sc.event_name" style="margin-left:16px">
          {{ sc.event_name }}: {{ sc.raw_value }} → {{ sc.earned_score }}分
        </div>
      </div>
    </el-card>

    <el-dialog v-model="showChangePwd" title="修改密码" width="350px">
      <el-form label-width="80px">
        <el-form-item label="原密码"><el-input v-model="oldPwd" type="password" /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="newPwd" type="password" /></el-form-item>
        <el-button type="primary" @click="changePassword">确认修改</el-button>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const schoolName = ref('体育成绩管理系统')
const studentInfo = ref({})
const currentScores = ref([])
const total = ref(0)
const maxTotal = ref(90)
const recommended = ref([])
const history = ref({})
const showChangePwd = ref(false)
const oldPwd = ref('')
const newPwd = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/config/public')
    schoolName.value = res.data.school_name || schoolName.value
  } catch {}

  const info = sessionStorage.getItem('student_info')
  if (!info) { router.push('/student/login'); return }
  studentInfo.value = JSON.parse(info)

  loadScores()
})

async function loadScores() {
  const res = await api.get('/student/scores', {
    params: {
      student_id: sessionStorage.getItem('student_id'),
      token: sessionStorage.getItem('student_token')
    }
  })
  currentScores.value = res.data.current_scores
  total.value = res.data.total
  maxTotal.value = res.data.max_total
  recommended.value = res.data.recommended
  history.value = res.data.history_by_date
}

async function changePassword() {
  try {
    await api.put('/student/password', {
      old_password: oldPwd.value,
      new_password: newPwd.value
    }, {
      params: {
        student_id: sessionStorage.getItem('student_id'),
        token: sessionStorage.getItem('student_token')
      }
    })
    ElMessage.success('密码修改成功')
    showChangePwd.value = false
  } catch { ElMessage.error('修改失败') }
}

function logout() {
  sessionStorage.clear()
  router.push('/student/login')
}
</script>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/student/Login.vue frontend/src/views/student/Scores.vue
git commit -m "feat: student portal - login, score view, password change"
```

---

### Task 21: Integration & Final Testing

- [ ] **Step 1: Add database init on startup**

Edit `backend/app/main.py`, add after the CORS middleware setup (before include_router lines):

```python
from .database import engine, Base
from . import models

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 2: Run full backend test**

Run: `cd backend; python -m app.seed`
Expected: Seed data created.

Run: `cd backend; python -m uvicorn app.main:app --reload`
Manual: Open http://localhost:8000/docs, verify all API endpoints visible.

- [ ] **Step 3: Test frontend flows**

Run: `cd frontend; npm run dev`

Test flows:
1. Visit http://localhost:5173/admin/login → Login as admin/admin123
2. Navigate to 学生管理 → Verify list loads, import template downloads
3. Navigate to 成绩录入 → Select class/project → Enter scores → Verify real-time scoring and alerts
4. Navigate to 统计分析 → Select class → Verify stats and export
5. Navigate to 开发人员选项 → Verify events, admins, config
6. Visit http://localhost:5173/student/login → Login as a seeded student
7. Verify student scores view and password change

- [ ] **Step 4: Commit final integration changes**

```bash
git add backend/app/main.py
git commit -m "feat: auto-create tables on startup, integration complete"
```

---

## Appendix: Deployment Notes

1. Set environment variables: `DATABASE_URL=postgresql://...`, `SECRET_KEY=<random>`
2. Build frontend: `cd frontend; npm run build` → output goes to `dist/`
3. Option A: Serve static via FastAPI (`app.mount("/", StaticFiles(...))`)
4. Option B: Use Nginx reverse proxy for both API and static files
5. Run with: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
