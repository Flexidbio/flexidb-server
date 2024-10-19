from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
from app.api.auth import get_current_user

router = APIRouter()


def create_initial_user(username: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).first():
        raise HTTPException(status_code=400, detail="Initial user already exists")
    db_user = User(username=username, hashed_password=get_password_hash(password))
    db.add(db_user)
    db.commit()
    return {"message": "Initial user created successfully"}

@router.put("/users/me")
def update_user(password: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.hashed_password = get_password_hash(password)
    db.commit()
    return {"message": "User updated successfully"}


## uvicorn main:app --port "8000" --reload