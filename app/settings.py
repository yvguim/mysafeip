"""
External settings configuration
"""
import os
from pydantic import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    """
    External variables loaded from .env file
    """
    load_dotenv()

    DISABLE_REGISTER: bool = os.getenv('DISABLE_REGISTER')
    JWT_SECRET: str = os.getenv('JWT_SECRET')
    ALGORITHM: str = os.getenv('ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
    SQLALCHEMY_DATABASE_URI: str = os.getenv('SQLALCHEMY_DATABASE_URI')

settings = Settings()
