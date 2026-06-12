from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Admin, School
from ..schemas import AdminCreate, AdminUpdate, AdminOut
from ..auth import get_super_admin, get_school_admin, require_school, hash_password

router = APIRouter(prefix="/api/admins", tags=["admins"])

def _enrich(out: AdminOut, admin: Admin):
    if admin.school:
        out.school_name = admin.school.name
    elif admin.role == "super":
        out.school_name = "平台管理"
    return out

@router.get("", response_model=list[AdminOut])
def list_admins(
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_school_admin)
):
    if current.role == "super":
        q = db.query(Admin)
        if school_id is not None:
            q = q.filter(Admin.school_id == school_id)
    else:
        # School admin: only see their own school's non-super admins
        sid = require_school(current)
        q = db.query(Admin).filter(Admin.school_id == sid, Admin.role != "super")
    admins = q.order_by(Admin.id).all()
    return [_enrich(AdminOut.model_validate(a), a) for a in admins]

@router.post("", response_model=AdminOut)
def create_admin(data: AdminCreate, db: Session = Depends(get_db), current: Admin = Depends(get_school_admin)):
    existing = db.query(Admin).filter(Admin.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    if current.role == "super":
        # Super admin can create any role in any school
        role = getattr(data, 'role', None) or 'teacher'
        school_id = data.school_id
    else:
        # School admin can only create teachers in their own school
        sid = require_school(current)
        role = 'teacher'
        school_id = sid

    if role == "super":
        school_id = None  # super admins have no school

    admin = Admin(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        role=role,
        school_id=school_id
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return _enrich(AdminOut.model_validate(admin), admin)

@router.put("/{admin_id}", response_model=AdminOut)
def update_admin(admin_id: int, data: AdminUpdate, db: Session = Depends(get_db), current: Admin = Depends(get_school_admin)):
    admin = db.query(Admin).get(admin_id)
    if not admin:
        raise HTTPException(404, "管理员不存在")

    if current.role == "super":
        # Super admin can change role, school_id, display_name, password
        if data.display_name is not None:
            admin.display_name = data.display_name
        if data.password is not None:
            admin.password_hash = hash_password(data.password)
        if data.role is not None:
            if data.role not in ("super", "school_admin", "teacher"):
                raise HTTPException(400, "无效的角色")
            if admin.id == current.id and data.role != "super":
                raise HTTPException(400, "不能取消自己的超级管理员权限")
            admin.role = data.role
            if data.role == "super":
                admin.school_id = None
        if data.school_id is not None:
            admin.school_id = data.school_id
    else:
        # School admin can only update display_name/password of teachers in their own school
        if admin.role == "super" or admin.school_id != require_school(current):
            raise HTTPException(403, "无权限修改此管理员")
        if data.role is not None or data.school_id is not None:
            raise HTTPException(403, "仅超级管理员可修改角色和所属学校")
        if data.display_name is not None:
            admin.display_name = data.display_name
        if data.password is not None:
            admin.password_hash = hash_password(data.password)

    db.commit()
    db.refresh(admin)
    return _enrich(AdminOut.model_validate(admin), admin)

@router.delete("/{admin_id}")
def delete_admin(admin_id: int, db: Session = Depends(get_db), current: Admin = Depends(get_school_admin)):
    admin = db.query(Admin).get(admin_id)
    if not admin:
        raise HTTPException(404)
    if admin.id == current.id:
        raise HTTPException(400, detail="不能删除自己")
    if admin.role == "super":
        raise HTTPException(403, detail="不能删除超级管理员")

    if current.role != "super":
        # School admin can only delete teachers in their own school
        if admin.school_id != require_school(current):
            raise HTTPException(403, detail="无权限删除此管理员")

    db.delete(admin)
    db.commit()
    return {"ok": True}
