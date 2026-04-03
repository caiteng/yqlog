import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

BASE_DIR = Path(__file__).resolve().parent

# 优先检查容器内覆盖配置，再检查宿主机固定路径
EXTERNAL_CONFIG_PATHS: List[Path] = [
    Path("/app/config.override.yml"),
    Path("/opt/yqlog/config.yml"),
]
PROJECT_DEFAULT_CONFIG_PATH = BASE_DIR / "config.default.yml"

CODE_DEFAULT_CONFIG: Dict[str, Any] = {
    "app": {
        "app_name": "语沁成长记录",
        "secret_key": "yqlog-dev-secret",
    },
    "security": {
        "access_password": "无敌可爱语沁",
        "session_days": 1,
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
    },
    "database": {
        "sqlite_path": str(BASE_DIR / "data" / "yqlog.db"),
    },
    "storage": {
        "upload_dir": str(BASE_DIR / "uploads"),
        "album_max_photos": 200,
        "max_image_size_bytes": 10 * 1024 * 1024,
        "max_content_length": 60 * 1024 * 1024,
        "allowed_extensions": ["png", "jpg", "jpeg", "webp", "gif"],
    },
    "stats": {
        "milk_days": 30,
        "poop_days": 30,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_config_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(content)
    else:
        data = yaml.safe_load(content) or {}

    if not isinstance(data, dict):
        raise ValueError(f"配置文件格式错误（必须是对象/字典）：{path}")
    return data


def _pick_external_config() -> Path | None:
    for path in EXTERNAL_CONFIG_PATHS:
        if path.exists():
            return path
    return None


def load_config() -> Dict[str, Any]:
    config = dict(CODE_DEFAULT_CONFIG)

    if PROJECT_DEFAULT_CONFIG_PATH.exists():
        config = _deep_merge(config, _read_config_file(PROJECT_DEFAULT_CONFIG_PATH))

    external_path = _pick_external_config()
    if external_path:
        config = _deep_merge(config, _read_config_file(external_path))

    return config


class Config:
    """Flask 配置映射。"""

    _raw = load_config()

    APP_NAME = _raw["app"]["app_name"]
    SECRET_KEY = _raw["app"]["secret_key"]

    ACCESS_PASSWORD = _raw["security"]["access_password"]
    SESSION_DAYS = int(_raw["security"]["session_days"])

    HOST = _raw["server"]["host"]
    PORT = int(_raw["server"]["port"])

    DATABASE_PATH = Path(_raw["database"]["sqlite_path"])

    UPLOAD_FOLDER = Path(_raw["storage"]["upload_dir"])
    ALBUM_MAX_PHOTOS = int(_raw["storage"]["album_max_photos"])
    MAX_IMAGE_SIZE_BYTES = int(_raw["storage"]["max_image_size_bytes"])
    MAX_CONTENT_LENGTH = int(_raw["storage"]["max_content_length"])
    ALLOWED_EXTENSIONS = set(_raw["storage"]["allowed_extensions"])

    MILK_STATS_DAYS = int(_raw["stats"]["milk_days"])
    POOP_STATS_DAYS = int(_raw["stats"]["poop_days"])
