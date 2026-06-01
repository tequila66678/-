from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Student, Score, SportEvent, Class
from ..schemas import StudentLogin, StudentPasswordChange
from ..auth import hash_password, verify_student_password
from ..scoring import parse_value
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
    school_id = None
    if student.class_ and student.class_.school_id:
        school_id = student.class_.school_id
    return {
        "token": f"student_{student.id}",
        "school_id": school_id,
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name,
            "gender": student.gender.value,
            "class_name": student.class_.name if student.class_ else "",
            "class_grade": student.class_.grade if student.class_ else "",
        }
    }

def _get_student_from_token(db: Session, student_id: str, token: str) -> Student:
    if not token.startswith("student_"):
        raise HTTPException(401, "无效的登录凭证")
    db_id = int(token.split("_")[1])
    student = db.query(Student).get(db_id)
    if not student or student.student_id != student_id:
        raise HTTPException(401, "无效的登录凭证")
    return student

@router.get("/scores")
def get_my_scores(student_id: str, token: str, db: Session = Depends(get_db)):
    student = _get_student_from_token(db, student_id, token)

    scores = db.query(Score).filter(Score.student_id == student.id).order_by(Score.test_date.desc()).all()
    events = {e.id: e for e in db.query(SportEvent).all()}

    by_date = defaultdict(list)
    for sc in scores:
        event = events.get(sc.event_id)
        try:
            nv = parse_value(sc.raw_value, event.input_format) if event else None
        except (ValueError, AttributeError):
            nv = None
        by_date[sc.test_date.isoformat()].append({
            "event_name": events[sc.event_id].name if sc.event_id in events else "未知",
            "raw_value": sc.raw_value,
            "earned_score": sc.earned_score,
            "numeric_value": nv,
            "unit": event.unit if event else "",
            "higher_better": event.higher_better if event else True
        })

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
    student = _get_student_from_token(db, student_id, token)

    if not verify_student_password(data.old_password, student.password_hash):
        raise HTTPException(400, "原密码错误")

    student.password_hash = hash_password(data.new_password)
    db.commit()
    return {"ok": True}
