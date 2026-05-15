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
    grade = Column(String, nullable=False)
    name = Column(String, nullable=False)
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
    gender = Column(SqlEnum(Gender), nullable=False, default="both")
    score = Column(Integer, nullable=False)
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
