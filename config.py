import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Central configuration class.
    Reads sensitive values from environment variables (.env file) instead
    of hardcoding them — required practice for any security-focused project.
    """
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-do-not-use-in-production")

    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "ztxai_db")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
