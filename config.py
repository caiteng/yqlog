import os
from pathlib import Path
from typing import Any, Dict

import yaml

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DEFAULT_CONFIG_PATH = BASE_DIR / "config.default.yml"
SERVER_FIXED_CONFIG_PATH = Path("/opt/yqlog/config.yml")
CONTAINER_OVERRIDE_CONFIG_PATH = Path("/app/config.override.yml")


CODE_DEFAULTS: Dict[str, Any] = {
    "SECRET_KEY": "yqlog-dev-secret",
    "ACCESS_PASSWORD": "无敌可爱语沁",
    "SESSION_DAYS": 1,
    "DATABASE_PATH": str(BASE_DIR / "data" / "yqlog.db"),
    "UPLOAD_FOLDER": str(BASE_DIR / "uploads"),
    "ALBUM_MAX_PHOTOS": 200,
    "MAX_IMAGE_SIZE_BYTES": 10 * 1024 * 1024,
    "MAX_CONTENT_LENGTH": 60 * 1024 * 1024,
    "ALLOWED_EXTENSIONS": ["png", "jpg", "jpeg", "webp", "gif"],
}


def _load_yaml_file(path: Path) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"配置文件格式错误，必须是键值对象: {path}")

    return data


def _discover_override_path() -> Path:
    override_env = os.getenv("CONFIG_OVERRIDE_PATH")
    if override_env:
        return Path(override_env)

    if CONTAINER_OVERRIDE_CONFIG_PATH.exists():
        return CONTAINER_OVERRIDE_CONFIG_PATH

    return SERVER_FIXED_CONFIG_PATH


def load_app_config() -> Dict[str, Any]:
    project_default_path = Path(
        os.getenv("PROJECT_DEFAULT_CONFIG_PATH", str(PROJECT_DEFAULT_CONFIG_PATH))
    )
    override_path = _discover_override_path()

    merged = dict(CODE_DEFAULTS)
    merged.update(_load_yaml_file(project_default_path))
    merged.update(_load_yaml_file(override_path))

    return {
        "SECRET_KEY": str(merged["SECRET_KEY"]),
        "ACCESS_PASSWORD": str(merged["ACCESS_PASSWORD"]),
        "SESSION_DAYS": int(merged["SESSION_DAYS"]),
        "DATABASE_PATH": Path(str(merged["DATABASE_PATH"])),
        "UPLOAD_FOLDER": Path(str(merged["UPLOAD_FOLDER"])),
        "ALBUM_MAX_PHOTOS": int(merged["ALBUM_MAX_PHOTOS"]),
        "MAX_IMAGE_SIZE_BYTES": int(merged["MAX_IMAGE_SIZE_BYTES"]),
        "MAX_CONTENT_LENGTH": int(merged["MAX_CONTENT_LENGTH"]),
        "ALLOWED_EXTENSIONS": {str(ext).lower() for ext in merged["ALLOWED_EXTENSIONS"]},
    }


class Config:
    """应用基础配置（优先级：服务器覆盖 > 项目默认 > 代码默认）。"""


for key, value in load_app_config().items():
    setattr(Config, key, value)
