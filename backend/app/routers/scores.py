from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Score, Student, SportEvent, ScoringStandard, Class, Admin, SystemConfig, InputFormat
from ..schemas import ScoreBatchSave, ScoreWithChange
from ..auth import get_current_admin
from ..scoring import calculate_score, normalize_time_ms
import openpyxl
from io import BytesIO
from datetime import date
from typing import Optional
from collections import defaultdict

router = APIRouter(prefix="/api/scores", tags=["scores"])

def _get_previous_score(db: Session, student_db_id: int, event_id: int, current_date: date) -> Optional[Score]:
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
    praise_threshold = 1
    warning_threshold = 2
    praise_cfg = db.query(SystemConfig).filter(SystemConfig.key == "praise_threshold").first()
    warning_cfg = db.query(SystemConfig).filter(SystemConfig.key == "warning_threshold").first()
    if praise_cfg:
        praise_threshold = int(praise_cfg.value)
    if warning_cfg:
        warning_threshold = int(warning_cfg.value)

    for entry in data.scores:
        event = db.query(SportEvent).get(entry.event_id)
        student = db.query(Student).get(entry.student_id)
        raw_value = entry.raw_value
        if event and event.input_format == InputFormat.time_ms:
            raw_value = normalize_time_ms(raw_value)
        standards = db.query(ScoringStandard).filter(ScoringStandard.event_id == entry.event_id).all()
        earned = calculate_score(raw_value, event, standards, student.gender.value if student else None)

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

        existing = (
            db.query(Score)
            .filter(
                Score.student_id == entry.student_id,
                Score.event_id == entry.event_id,
                Score.test_date == entry.test_date
            ).first()
        )
        if existing:
            existing.raw_value = raw_value
            existing.earned_score = earned
            existing.recorder_id = current.id
            score_obj = existing
        else:
            score_obj = Score(
                student_id=entry.student_id,
                event_id=entry.event_id,
                raw_value=raw_value,
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
    event_ids: Optional[str] = Query(None),
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

    all_scores = scores_q.order_by(Score.test_date.desc()).all()
    latest = {}
    for sc in all_scores:
        key = (sc.student_id, sc.event_id)
        if key not in latest:
            latest[key] = sc

    events = db.query(SportEvent).all()
    if event_id_list:
        events = [e for e in events if e.id in event_id_list]

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
    excellent_count = sum(1 for t in total_scores if max_per_student > 0 and t / max_per_student >= 9)
    pass_count = sum(1 for t in total_scores if max_per_student > 0 and t / max_per_student >= 6)
    n_students = len(student_totals)

    warning_students = []
    for s in students:
        for e in events:
            student_scores = sorted(
                [sc for sc in all_scores if sc.student_id == s.id and sc.event_id == e.id],
                key=lambda x: x.test_date
            )
            if len(student_scores) >= 2:
                prev_score = student_scores[-2].earned_score
                curr_score = student_scores[-1].earned_score
                if prev_score - curr_score >= 2:
                    warning_students.append({
                        "student_id": s.id,
                        "student_name": s.name,
                        "student_no": s.student_id,
                        "event_name": e.name,
                        "prev_score": prev_score,
                        "curr_score": curr_score
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
    event_id: int = Query(None),
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    q = db.query(Student).filter(Student.class_id == class_id)
    if event_id:
        event = db.query(SportEvent).get(event_id)
        if event and event.gender.value != "both":
            q = q.filter(Student.gender == event.gender)
    students = q.order_by(Student.student_id).all()
    return [{"id": s.id, "student_id": s.student_id, "name": s.name, "gender": s.gender.value} for s in students]
