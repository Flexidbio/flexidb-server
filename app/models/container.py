from sqlalchemy import Column, Integer, String, JSON
from app.core.database import Base

class Container(Base):
    __tablename__ = "containers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    db_type = Column(String)
    status = Column(String)
    env = Column(JSON)
    connection_string = Column(String)
    port = Column(Integer)
