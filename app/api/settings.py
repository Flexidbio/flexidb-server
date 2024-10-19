from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.app_settings import AppSettings
from app.api.auth import get_current_user
from pydantic import BaseModel
from app.models.user import User

router = APIRouter()

class SettingsUpdate(BaseModel):
    domain: str
    resend_api_key: str

@router.post("/settings")
def create_settings(settings: SettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if db.query(AppSettings).first():
        raise HTTPException(status_code=400, detail="Settings already exist")
    db_settings = AppSettings(domain=settings.domain, resend_api_key=settings.resend_api_key)
    db.add(db_settings)
    db.commit()
    return {"message": "Settings created successfully"}

@router.put("/settings")
def update_settings(settings: SettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_settings = db.query(AppSettings).first()
    if not db_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    db_settings.domain = settings.domain
    db_settings.resend_api_key = settings.resend_api_key
    db.commit()
    return {"message": "Settings updated successfully"}

@router.get("/settings")
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = db.query(AppSettings).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return {"domain": settings.domain, "resend_api_key": settings.resend_api_key}