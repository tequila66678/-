from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from .models import Gender, InputFormat

# Auth
class AdminLogin(BaseModel):
    username: str
    password: str

class AdminOut(BaseModel):
    id: int
    username: str
    display_name: str
    is_super: bool = False  # deprecated, kept for backward compat with frontend
    role: str = "teacher"
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    model_config = {"from_attributes": True}

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminOut

# Student
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

# Class
class ClassOut(BaseModel):
    id: int
    grade: str
    name: str
    model_config = {"from_attributes": True}

# SportEvent
class ScoringStandardOut(BaseModel):
    id: int
    gender: str = "both"
    score: int
    standard_value: str
    model_config = {"from_attributes": True}

class ScoringStandardUpdate(BaseModel):
    gender: str = "both"
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

# Score
class ScoreEntry(BaseModel):
    student_id: int
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
    previous_score: Optional[int] = None
    change: Optional[int] = None
    is_praise: bool = False
    is_warning: bool = False

class DistributionBucket(BaseModel):
    label: str
    count: int

class EventAvgScore(BaseModel):
    event_id: int
    event_name: str
    avg_score: float
    count: int = 0

class ClassStatsOut(BaseModel):
    class_id: int
    class_name: str
    total_students: int
    participants: int = 0
    avg_score: float
    excellent_rate: float
    pass_rate: float
    full_score_rate: float = 0
    score_distribution: list[DistributionBucket] = []
    event_avgs: list[EventAvgScore] = []
    warning_students: list[dict] = []

class StudentStatsOut(BaseModel):
    student: StudentOut
    scores_by_event: dict[str, list[ScoreOut]]
    recommended_events: list[dict]

class ClearAllRequest(BaseModel):
    password: str

# Admin
class AdminCreate(BaseModel):
    username: str
    password: str
    display_name: str
    is_super: bool = False  # deprecated, use role
    role: str = "teacher"
    school_id: Optional[int] = None

class AdminUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    school_id: Optional[int] = None

# Config
class ConfigUpdate(BaseModel):
    value: str

class ConfigOut(BaseModel):
    key: str
    value: str
    model_config = {"from_attributes": True}

# Student Portal
class StudentLogin(BaseModel):
    student_id: str
    password: str

class StudentPasswordChange(BaseModel):
    old_password: str
    new_password: str

# School
class SchoolOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}

class SchoolCreate(BaseModel):
    name: str

class SwitchSchoolRequest(BaseModel):
    school_id: Optional[int] = None
