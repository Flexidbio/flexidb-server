from pydantic import BaseModel

class Settings(BaseModel):
    DATABASE_URL: str = "sqlite:///./flexidb.db"
    SECRET_KEY: str = "3e4bb0d562f8853f7133d0e0"  # Change this in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    domain: str = "localhost"
    class Config:
        env_file = ".env"

settings = Settings()
