from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """应用基础配置（轻量单机场景）。"""

    SECRET_KEY = "yqlog-dev-secret"
    ACCESS_PASSWORD = "无敌可爱语沁"
    SESSION_DAYS = 1

    DATABASE_PATH = BASE_DIR / "data" / "yqlog.db"
    UPLOAD_FOLDER = BASE_DIR / "uploads"

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
