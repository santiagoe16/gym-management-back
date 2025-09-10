from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Gym Management"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DB_URL: str
    
    @property
    def DATABASE_URL(self) -> str:
        return self.DB_URL
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int] = None  # No expiration - users stay logged in until logout
    
    # Application
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    ADMIN_NAME: str
    ADMIN_PASSWORD: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings() 