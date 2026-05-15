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
