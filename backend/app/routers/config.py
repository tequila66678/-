from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SystemConfig, Admin
from ..schemas import ConfigUpdate, ConfigOut
from ..auth import get_super_admin

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("", response_model=list[ConfigOut])
def list_config(db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    return db.query(SystemConfig).all()

@router.get("/public")
def get_public_config(db: Session = Depends(get_db)):
    configs = db.query(SystemConfig).all()
    result = {}
    for c in configs:
        if c.key in ("school_name", "designer"):
            result[c.key] = c.value
    return result

@router.put("/{key}")
def update_config(key: str, data: ConfigUpdate, db: Session = Depends(get_db), current: Admin = Depends(get_super_admin)):
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        config = SystemConfig(key=key, value=data.value)
        db.add(config)
    else:
        config.value = data.value
    db.commit()
    return {"ok": True, "key": key, "value": data.value}
