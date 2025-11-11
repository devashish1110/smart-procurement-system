"""
Application Settings and Configuration
File: backend/config/settings.py
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    APP_NAME: str = "Smart Procurement System"
    APP_VERSION: str = "1.0.0"
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME", "procurement")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:5173"
    ).split(",")
    
    # AI/ML
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # WhatsApp
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    
    # File Upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 5242880))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    
    # Inventory Settings
    LOW_STOCK_THRESHOLD: int = 10
    EXPIRY_WARNING_DAYS: int = 90
    CRITICAL_EXPIRY_DAYS: int = 30
    
    # Procurement Settings
    AUTO_APPROVE_THRESHOLD: float = 5000.0  # Auto-approve POs below this amount
    VENDOR_RATING_THRESHOLD: float = 3.5    # Minimum vendor rating
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()


# Validate critical settings on startup
def validate_settings():
    """Validate that all critical settings are present"""
    critical_settings = [
        "DATABASE_URL",
        "SECRET_KEY",
        "GROQ_API_KEY"
    ]
    
    missing = []
    for setting in critical_settings:
        if not getattr(settings, setting, None):
            missing.append(setting)
    
    if missing:
        raise ValueError(
            f"Missing critical environment variables: {', '.join(missing)}\n"
            "Please check your .env file."
        )
    
    print("✓ All critical settings validated")
    return True