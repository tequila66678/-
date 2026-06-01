from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SportEvent, ScoringStandard, Class, Admin
from ..schemas import (
    SportEventCreate, SportEventUpdate, SportEventOut,
    ScoringStandardUpdate
)
from ..auth import get_super_admin, get_current_admin, require_school

router = APIRouter(prefix="/api/events", tags=["events"])

def _school_filter(q, school_id):
    if school_id is not None:
        return q.filter(SportEvent.school_id == school_id)
    return q

@router.get("", response_model=list[SportEventOut])
def list_events(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    sid = require_school(current)
    return _school_filter(db.query(SportEvent), sid).order_by(SportEvent.sort_order).all()

@router.post("", response_model=SportEventOut)
def create_event(data: SportEventCreate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    sid = require_school(current)
    event = SportEvent(**data.model_dump(), school_id=sid)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.put("/{event_id}", response_model=SportEventOut)
def update_event(event_id: int, data: SportEventUpdate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    sid = require_school(current)
    event = _school_filter(db.query(SportEvent), sid).filter(SportEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="项目不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(event, key, val)
    db.commit()
    db.refresh(event)
    return event

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    sid = require_school(current)
    event = _school_filter(db.query(SportEvent), sid).filter(SportEvent.id == event_id).first()
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
    sid = require_school(current)
    event = _school_filter(db.query(SportEvent), sid).filter(SportEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.query(ScoringStandard).filter(ScoringStandard.event_id == event_id).delete()
    for s in standards:
        gender_val = s.gender if s.gender in ("M", "F", "both") else "both"
        std = ScoringStandard(event_id=event_id, gender=gender_val, score=s.score, standard_value=s.standard_value)
        db.add(std)
    db.commit()
    return {"ok": True, "count": len(standards)}

@router.get("/classes", response_model=list[dict])
def list_classes(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    sid = require_school(current)
    classes = db.query(Class).filter(Class.school_id == sid).order_by(Class.grade, Class.name).all()
    return [{"id": c.id, "grade": c.grade, "name": c.name, "label": f"{c.grade}{c.name}"} for c in classes]
