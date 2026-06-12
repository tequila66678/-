from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import Admin

bearer_scheme = HTTPBearer()
optional_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_jwt(admin_id: int, username: str, school_id: Optional[int] = None) -> str:
    payload = {
        "sub": str(admin_id),
        "username": username,
        "school_id": school_id,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Admin:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        admin_id = int(payload.get("sub"))
        school_id = payload.get("school_id")
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录凭证")

    admin = db.query(Admin).get(admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="管理员不存在")
    admin.current_school_id = school_id
    return admin

def get_super_admin(current: Admin = Depends(get_current_admin)) -> Admin:
    if current.role != "super":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限")
    return current

def get_school_admin(current: Admin = Depends(get_current_admin)) -> Admin:
    """Super admin or school admin — for settings page access."""
    if current.role not in ("super", "school_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要学校管理员权限")
    return current

def get_school_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Optional[int]:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("school_id")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录凭证")

def require_school(current: Admin = Depends(get_current_admin)) -> Optional[int]:
    """Get current admin's school_id for filtering.
    Super-admin with no school → None (see all schools).
    Regular admin with no school → error."""
    sid = getattr(current, "current_school_id", None)
    if sid is None and current.role != "super":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先选择学校")
    return sid  # None for super-admin = see all schools

def get_current_admin_flexible(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Admin:
    """Auth for file downloads: tries Bearer header first, then ?token= query param."""
    for t in ([credentials.credentials] if credentials else []) + ([token] if token else []):
        try:
            payload = jwt.decode(t, settings.secret_key, algorithms=[settings.jwt_algorithm])
            admin_id = int(payload.get("sub"))
            admin = db.query(Admin).get(admin_id)
            if admin:
                admin.current_school_id = payload.get("school_id")
                return admin
        except (JWTError, ValueError, TypeError):
            continue
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录凭证")

def verify_student_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
