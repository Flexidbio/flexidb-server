from fastapi import FastAPI, Request
from app.api import containers, health, auth, user ,settings
from app.core.database import engine, Base ,get_db
from fastapi.middleware.cors import CORSMiddleware
from app.api.user import create_initial_user
from app.models.user import User
import logging
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FlexiDB API")
origins = [
    "http://localhost:3000",
    "https://your-frontend-domain.com",  # Add your production frontend URL if applicable
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Replace "*" with specific domains for better security, e.g., ["http://188.245.185.241:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers (Authorization, Content-Type, etc.)
)

@app.on_event("startup")
def check_initial_user():
    db: Session = next(get_db())  # Manually get a database session
    if not db.query(User).first():
        username = "admin"  # You can use environment variables for these values
        password = "admin"
        create_initial_user(username=username, password=password, db=db)
        print("Initial user created successfully")
app.include_router(health.router)
app.include_router(containers.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(settings.router)