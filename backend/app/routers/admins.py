from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Admin, School
from ..schemas import AdminCreate, AdminUpdate, AdminOut
from ..auth import get_super_admin, require_school, hash_password

router = APIRouter(prefix="/api/admins", tags=["admins"])

def _enrich(out: AdminOut, admin: Admin):
    if admin.school:
        out.school_name = admin.school.name
    elif admin.is_super:
        out.school_name = "平台管理"
    return out

@router.get("", response_model=list[AdminOut])
def list_admins(
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_super_admin)
):
    q = db.query(Admin)
    if school_id is not None:
        q = q.filter(Admin.school_id == school_id)
    admins = q.order_by(Admin.id).all()
    return [_enrich(AdminOut.model_validate(a), a) for a in admins]

@router.post("", response_model=AdminOut)
def create_admin(data: AdminCreate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    existing = db.query(Admin).filter(Admin.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    admin = Admin(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        is_super=data.is_super,
        school_id=data.school_id
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return _enrich(AdminOut.model_validate(admin), admin)

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
    return _enrich(AdminOut.model_validate(admin), admin)

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
