from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SportEvent, ScoringStandard, Class, Admin
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
    db.query(ScoringStandard).filter(ScoringStandard.event_id == event_id).delete()
    for s in standards:
        gender_val = s.gender if s.gender in ("M", "F", "both") else "both"
        std = ScoringStandard(event_id=event_id, gender=gender_val, score=s.score, standard_value=s.standard_value)
        db.add(std)
    db.commit()
    return {"ok": True, "count": len(standards)}

@router.get("/classes", response_model=list[dict])
def list_classes(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    classes = db.query(Class).order_by(Class.grade, Class.name).all()
    return [{"id": c.id, "grade": c.grade, "name": c.name, "label": f"{c.grade}{c.name}"} for c in classes]
