from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Admin, School
from ..schemas import AdminLogin, AdminOut, TokenOut, SwitchSchoolRequest
from ..auth import verify_password, create_jwt, get_current_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenOut)
def login(data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == data.username).first()
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    # Auto-assign school for super-admin with no school
    school_id = admin.school_id
    if admin.is_super and not school_id:
        default_school = db.query(School).first()
        school_id = default_school.id if default_school else None
    token = create_jwt(admin.id, admin.username, school_id)
    out = AdminOut.model_validate(admin)
    if admin.school:
        out.school_name = admin.school.name
    elif school_id:
        default_school = db.query(School).get(school_id)
        out.school_name = default_school.name if default_school else "平台管理"
    else:
        out.school_name = "平台管理"
    return TokenOut(access_token=token, admin=out)

@router.get("/me", response_model=AdminOut)
def me(current: Admin = Depends(get_current_admin)):
    out = AdminOut.model_validate(current)
    if current.school:
        out.school_name = current.school.name
    return out

@router.post("/switch-school", response_model=TokenOut)
def switch_school(
    data: SwitchSchoolRequest,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_admin)
):
    if not current.is_super:
        raise HTTPException(403, "仅超级管理员可切换学校")
    school = db.query(School).get(data.school_id)
    if not school:
        raise HTTPException(404, "学校不存在")
    token = create_jwt(current.id, current.username, data.school_id)
    current.current_school_id = data.school_id
    out = AdminOut.model_validate(current)
    out.school_name = school.name
    return TokenOut(access_token=token, admin=out)
