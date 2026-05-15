from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Admin
from ..schemas import AdminLogin, AdminOut, TokenOut
from ..auth import verify_password, create_jwt, get_current_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenOut)
def login(data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == data.username).first()
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_jwt(admin.id, admin.username)
    return TokenOut(
        access_token=token,
        admin=AdminOut.model_validate(admin)
    )

@router.get("/me", response_model=AdminOut)
def me(current: Admin = Depends(get_current_admin)):
    return AdminOut.model_validate(current)
