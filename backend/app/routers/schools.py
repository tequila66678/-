from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import School, Admin, Class, Student, SportEvent, ScoringStandard, Score, SystemConfig
from ..schemas import SchoolOut, SchoolCreate
from ..auth import get_super_admin, verify_password

router = APIRouter(prefix="/api/schools", tags=["schools"])

@router.get("", response_model=list[SchoolOut])
def list_schools(db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    return db.query(School).order_by(School.id).all()

@router.post("", response_model=SchoolOut)
def create_school(data: SchoolCreate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    school = School(name=data.name)
    db.add(school)
    db.flush()

    from ..seed import seed_school
    seed_school(db, school.id)

    db.commit()
    db.refresh(school)
    return school

@router.put("/{school_id}", response_model=SchoolOut)
def update_school(school_id: int, data: SchoolCreate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    school = db.query(School).get(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    school.name = data.name
    db.commit()
    db.refresh(school)
    return school

@router.delete("/{school_id}")
def delete_school(school_id: int, password: str = "", db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    school = db.query(School).get(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    if not verify_password(password, current.password_hash):
        raise HTTPException(status_code=403, detail="密码错误")

    db.query(Score).filter(Score.school_id == school_id).delete(synchronize_session=False)
    db.query(ScoringStandard).filter(ScoringStandard.event_id.in_(
        db.query(SportEvent.id).filter(SportEvent.school_id == school_id)
    )).delete(synchronize_session=False)
    db.query(Student).filter(Student.class_id.in_(
        db.query(Class.id).filter(Class.school_id == school_id)
    )).delete(synchronize_session=False)
    db.query(SportEvent).filter(SportEvent.school_id == school_id).delete(synchronize_session=False)
    db.query(Class).filter(Class.school_id == school_id).delete(synchronize_session=False)
    db.query(Admin).filter(Admin.school_id == school_id).delete(synchronize_session=False)
    db.query(SystemConfig).filter(SystemConfig.school_id == school_id).delete(synchronize_session=False)
    db.delete(school)
    db.commit()
    return {"ok": True}
