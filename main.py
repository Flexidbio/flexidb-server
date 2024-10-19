from fastapi import FastAPI
from app.api import containers, health, auth, user ,settings
from app.core.database import engine, Base


Base.metadata.create_all(bind=engine)

app = FastAPI(title="FlexiDB API")

app.include_router(health.router)
app.include_router(containers.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(settings.router)