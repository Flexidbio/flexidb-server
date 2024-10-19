from sqlalchemy import Column, Integer, String
from app.core.database import Base

class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String)
    resend_api_key = Column(String)