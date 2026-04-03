import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """应用基础配置（轻量单机场景）。"""

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "yqlog-dev-secret")
    ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD", "无敌可爱语沁")
    SESSION_DAYS = int(os.getenv("SESSION_DAYS", "1"))

    DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "yqlog.db")))
    UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads")))

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
