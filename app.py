import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.permanent_session_lifetime = timedelta(days=app.config["SESSION_DAYS"])


@app.context_processor
def inject_app_config():
    return {"app_name": app.config["APP_NAME"]}


POOP_STATUS_OPTIONS = {"正常", "奶瓣", "酸臭"}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    db_path: Path = app.config["DATABASE_PATH"]
    upload_folder: Path = app.config["UPLOAD_FOLDER"]

    db_path.parent.mkdir(parents=True, exist_ok=True)
    upload_folder.mkdir(parents=True, exist_ok=True)

    with get_conn() as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS milk_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_time TEXT NOT NULL,
                milk_ml INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS poop_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_time TEXT NOT NULL,
                poop_status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS album_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_milk_record_time
            ON milk_records(record_time);

            CREATE INDEX IF NOT EXISTS idx_poop_record_time
            ON poop_records(record_time);

            CREATE INDEX IF NOT EXISTS idx_album_created_at
            ON album_photos(created_at);
            """
        )


def require_unlock(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not session.get("unlocked"):
            if is_api_request():
                return api_error("请先输入口令后再操作", status=401)
            flash("请先输入口令后再进行录入", "warning")
            return redirect(url_for("unlock", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def allowed_file(filename: str) -> bool:
    allowed_extensions = app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def normalize_record_time(raw_value: str) -> str:
    parsed = datetime.strptime(raw_value, "%Y-%m-%dT%H:%M")
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def record_time_input_default() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def is_api_request() -> bool:
    return request.path.startswith("/api/")


def api_ok(data: Dict[str, Any], status: int = 200):
    return jsonify({"ok": True, **data}), status


def api_error(message: str, status: int = 400):
    return jsonify({"ok": False, "message": message}), status


def query_dashboard() -> Dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")

    with get_conn() as conn:
        milk_today = conn.execute(
            """
            SELECT COUNT(*) AS count,
                   COALESCE(SUM(milk_ml), 0) AS total_ml,
                   MAX(record_time) AS last_time
            FROM milk_records
            WHERE DATE(record_time) = ?
            """,
            (today,),
        ).fetchone()

        milk_daily = conn.execute(
            """
            SELECT DATE(record_time) AS day,
                   COUNT(*) AS times,
                   COALESCE(SUM(milk_ml), 0) AS total_ml
            FROM milk_records
            WHERE DATE(record_time) >= DATE('now', ?)
            GROUP BY DATE(record_time)
            ORDER BY day ASC
            """,
            (f"-{app.config['MILK_STATS_DAYS'] - 1} day",),
        ).fetchall()

        poop_today = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM poop_records
            WHERE DATE(record_time) = ?
            """,
            (today,),
        ).fetchone()

        poop_last = conn.execute(
            """
            SELECT record_time
            FROM poop_records
            ORDER BY record_time DESC
            LIMIT 1
            """
        ).fetchone()

        poop_daily = conn.execute(
            """
            SELECT DATE(record_time) AS day,
                   COUNT(*) AS times
            FROM poop_records
            WHERE DATE(record_time) >= DATE('now', ?)
            GROUP BY DATE(record_time)
            ORDER BY day ASC
            """,
            (f"-{app.config['POOP_STATS_DAYS'] - 1} day",),
        ).fetchall()

        poop_status = conn.execute(
            """
            SELECT poop_status,
                   COUNT(*) AS count
            FROM poop_records
            WHERE DATE(record_time) >= DATE('now', ?)
            GROUP BY poop_status
            """,
            (f"-{app.config['POOP_STATS_DAYS'] - 1} day",),
        ).fetchall()

        recent_photos = conn.execute(
            """
            SELECT id, image_path, created_at
            FROM album_photos
            ORDER BY created_at DESC
            LIMIT 6
            """
        ).fetchall()

    poop_status_map = {row["poop_status"]: row["count"] for row in poop_status}

    return {
        "today": {
            "milk_count": milk_today["count"] if milk_today else 0,
            "milk_total_ml": milk_today["total_ml"] if milk_today else 0,
            "last_milk_time": milk_today["last_time"] if milk_today else None,
            "today_poop_count": poop_today["count"] if poop_today else 0,
            "last_poop_time": poop_last["record_time"] if poop_last else None,
        },
        "milk_chart": [dict(row) for row in milk_daily],
        "poop_chart": [dict(row) for row in poop_daily],
        "poop_status": {
            "正常": poop_status_map.get("正常", 0),
            "奶瓣": poop_status_map.get("奶瓣", 0),
            "酸臭": poop_status_map.get("酸臭", 0),
        },
        "recent_photos": [dict(row) for row in recent_photos],
    }


def query_timeline() -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []

    with get_conn() as conn:
        milk_rows = conn.execute(
            """
            SELECT id, record_time, milk_ml
            FROM milk_records
            ORDER BY record_time DESC
            LIMIT 50
            """
        ).fetchall()

        poop_rows = conn.execute(
            """
            SELECT id, record_time, poop_status
            FROM poop_records
            ORDER BY record_time DESC
            LIMIT 50
            """
        ).fetchall()

    for row in milk_rows:
        events.append(
            {
                "id": row["id"],
                "time": row["record_time"],
                "type": "喝奶",
                "detail": f"喝奶 {row['milk_ml']} ML",
                "record_kind": "milk",
            }
        )

    for row in poop_rows:
        events.append(
            {
                "id": row["id"],
                "time": row["record_time"],
                "type": "拉臭臭",
                "detail": f"状态：{row['poop_status']}",
                "record_kind": "poop",
            }
        )

    events.sort(key=lambda item: item["time"], reverse=True)
    return events[:100]


def create_milk_record(record_time: str, milk_ml: int) -> None:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO milk_records (record_time, milk_ml, created_at) VALUES (?, ?, ?)",
            (record_time, milk_ml, now),
        )


def create_poop_record(record_time: str, poop_status: str) -> None:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO poop_records (record_time, poop_status, created_at) VALUES (?, ?, ?)",
            (record_time, poop_status, now),
        )


def delete_milk_record(record_id: int) -> bool:
    with get_conn() as conn:
        result = conn.execute("DELETE FROM milk_records WHERE id = ?", (record_id,))
        return result.rowcount > 0


def delete_poop_record(record_id: int) -> bool:
    with get_conn() as conn:
        result = conn.execute("DELETE FROM poop_records WHERE id = ?", (record_id,))
        return result.rowcount > 0


def list_album_photos(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        query = """
            SELECT id, image_path, created_at
            FROM album_photos
            ORDER BY created_at DESC
        """
        params: Tuple[Any, ...] = ()
        if limit:
            query += " LIMIT ?"
            params = (limit,)
        photos = conn.execute(query, params).fetchall()
    return [dict(row) for row in photos]


def get_album_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS count FROM album_photos").fetchone()
    return row["count"] if row else 0


def file_size_bytes(file: FileStorage) -> int:
    if file.content_length is not None:
        return file.content_length

    stream = file.stream
    current_position = stream.tell()
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(current_position)
    return size


def upload_album_photos(files: List[FileStorage]) -> Dict[str, Any]:
    if not files:
        return {"saved": 0, "warnings": ["请选择要上传的照片"], "limit_reached": False}

    now = datetime.utcnow().isoformat()
    saved = 0
    warnings: List[str] = []
    limit_reached = False
    max_count = app.config["ALBUM_MAX_PHOTOS"]
    max_image_size = app.config["MAX_IMAGE_SIZE_BYTES"]

    with get_conn() as conn:
        album_count = get_album_count(conn)
        for file in files:
            if not file or not file.filename:
                continue

            if album_count >= max_count:
                limit_reached = True
                warnings.append(f"相册最多允许 {max_count} 张照片，请先删除照片，再继续上传")
                break

            if not allowed_file(file.filename):
                warnings.append(f"文件 {file.filename} 格式不支持，已跳过")
                continue

            if file_size_bytes(file) > max_image_size:
                warnings.append(
                    f"文件 {file.filename} 超过单张大小限制（{max_image_size // (1024 * 1024)}MB），已跳过"
                )
                continue

            safe_name = secure_filename(file.filename)
            unique_name = f"album_{int(datetime.utcnow().timestamp() * 1000)}_{safe_name}"
            file.save(app.config["UPLOAD_FOLDER"] / unique_name)
            conn.execute(
                "INSERT INTO album_photos (image_path, created_at) VALUES (?, ?)",
                (unique_name, now),
            )
            saved += 1
            album_count += 1

    return {
        "saved": saved,
        "warnings": warnings,
        "limit_reached": limit_reached,
        "album_max_photos": max_count,
    }


def delete_album_photo(photo_id: int) -> bool:
    with get_conn() as conn:
        photo = conn.execute(
            "SELECT id, image_path FROM album_photos WHERE id = ?",
            (photo_id,),
        ).fetchone()

        if not photo:
            return False

        conn.execute("DELETE FROM album_photos WHERE id = ?", (photo_id,))

    file_path = app.config["UPLOAD_FOLDER"] / photo["image_path"]
    if file_path.exists():
        file_path.unlink()
    return True


@app.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(_: RequestEntityTooLarge):
    message = "上传请求太大，请减少单次上传数量或图片体积"
    if is_api_request():
        return api_error(message, status=413)
    flash(message, "error")
    return redirect(url_for("album"))


@app.route("/")
def index():
    dashboard = query_dashboard()
    return render_template("index.html", dashboard=dashboard)


@app.route("/timeline")
@require_unlock
def timeline():
    records = query_timeline()
    return render_template("timeline.html", records=records)


@app.route("/unlock", methods=["GET", "POST"])
def unlock():
    next_url = request.args.get("next") or request.form.get("next") or url_for("quick_entry")

    if request.method == "POST":
        password = request.form.get("password", "")
        if password == app.config["ACCESS_PASSWORD"]:
            session.permanent = True
            session["unlocked"] = True
            flash("口令验证成功，设备已解锁 24 小时", "success")
            return redirect(next_url)

        flash("口令不正确，请重试", "error")

    return render_template("unlock.html", next_url=next_url)


@app.route("/submit")
@require_unlock
def submit_redirect():
    return redirect(url_for("quick_entry"))


@app.route("/quick")
@require_unlock
def quick_entry():
    return render_template("quick.html")


@app.route("/record/milk", methods=["GET", "POST"])
@require_unlock
def milk_record():
    if request.method == "POST":
        record_time_raw = request.form.get("record_time", "").strip()
        milk_ml_raw = request.form.get("milk_ml", "").strip()

        if not record_time_raw or not milk_ml_raw:
            flash("请填写时间和 ML 数", "error")
            return redirect(url_for("milk_record"))

        try:
            record_time = normalize_record_time(record_time_raw)
            milk_ml = int(milk_ml_raw)
        except ValueError:
            flash("请输入正确的时间和 ML 数（整数）", "error")
            return redirect(url_for("milk_record"))

        if milk_ml <= 0:
            flash("ML 数需要大于 0", "error")
            return redirect(url_for("milk_record"))

        create_milk_record(record_time, milk_ml)

        flash("喝奶记录已保存", "success")
        return redirect(url_for("quick_entry"))

    return render_template("milk.html", default_time=record_time_input_default())


@app.route("/record/poop", methods=["GET", "POST"])
@require_unlock
def poop_record():
    if request.method == "POST":
        record_time_raw = request.form.get("record_time", "").strip()
        poop_status = request.form.get("poop_status", "").strip()

        if not record_time_raw or not poop_status:
            flash("请填写时间并选择状态", "error")
            return redirect(url_for("poop_record"))

        if poop_status not in POOP_STATUS_OPTIONS:
            flash("状态不支持，请重新选择", "error")
            return redirect(url_for("poop_record"))

        try:
            record_time = normalize_record_time(record_time_raw)
        except ValueError:
            flash("时间格式不正确", "error")
            return redirect(url_for("poop_record"))

        create_poop_record(record_time, poop_status)

        flash("拉臭臭记录已保存", "success")
        return redirect(url_for("quick_entry"))

    return render_template("poop.html", default_time=record_time_input_default())


@app.route("/record/milk/<int:record_id>/delete", methods=["POST"])
@require_unlock
def milk_record_delete(record_id: int):
    deleted = delete_milk_record(record_id)
    if not deleted:
        flash("喝奶记录不存在或已删除", "warning")
    else:
        flash("喝奶记录已删除", "success")
    return redirect(url_for("timeline"))


@app.route("/record/poop/<int:record_id>/delete", methods=["POST"])
@require_unlock
def poop_record_delete(record_id: int):
    deleted = delete_poop_record(record_id)
    if not deleted:
        flash("拉臭臭记录不存在或已删除", "warning")
    else:
        flash("拉臭臭记录已删除", "success")
    return redirect(url_for("timeline"))


@app.route("/album")
@require_unlock
def album():
    photos = list_album_photos()
    return render_template(
        "album.html",
        photos=photos,
        album_max_photos=app.config["ALBUM_MAX_PHOTOS"],
        album_current_count=len(photos),
        max_image_size_mb=app.config["MAX_IMAGE_SIZE_BYTES"] // (1024 * 1024),
    )


@app.route("/album/upload", methods=["POST"])
@require_unlock
def album_upload():
    files = request.files.getlist("photos")
    result = upload_album_photos(files)

    if result["saved"]:
        flash(f"已上传 {result['saved']} 张照片", "success")
    for warning in result["warnings"]:
        flash(warning, "warning")

    return redirect(url_for("album"))


@app.route("/album/delete/<int:photo_id>", methods=["POST"])
@require_unlock
def album_delete(photo_id: int):
    deleted = delete_album_photo(photo_id)
    if not deleted:
        flash("照片不存在", "warning")
        return redirect(url_for("album"))

    flash("照片已删除", "success")
    return redirect(url_for("album"))


@app.route("/api/v1/dashboard", methods=["GET"])
def api_dashboard():
    return api_ok({"data": query_dashboard()})


@app.route("/api/v1/records/milk", methods=["POST"])
@require_unlock
def api_create_milk_record():
    payload = request.get_json(silent=True) or {}
    record_time_raw = str(payload.get("record_time", "")).strip()
    milk_ml_raw = payload.get("milk_ml", "")

    if not record_time_raw or milk_ml_raw == "":
        return api_error("请提供 record_time 和 milk_ml")

    try:
        record_time = normalize_record_time(record_time_raw)
        milk_ml = int(milk_ml_raw)
    except ValueError:
        return api_error("record_time 格式需为 YYYY-MM-DDTHH:MM，milk_ml 必须是整数")

    if milk_ml <= 0:
        return api_error("milk_ml 必须大于 0")

    create_milk_record(record_time, milk_ml)
    return api_ok({"message": "喝奶记录已保存"}, status=201)


@app.route("/api/v1/records/milk/<int:record_id>", methods=["DELETE"])
@require_unlock
def api_delete_milk_record(record_id: int):
    deleted = delete_milk_record(record_id)
    if not deleted:
        return api_error("喝奶记录不存在", status=404)
    return api_ok({"message": "喝奶记录已删除"})


@app.route("/api/v1/records/poop", methods=["POST"])
@require_unlock
def api_create_poop_record():
    payload = request.get_json(silent=True) or {}
    record_time_raw = str(payload.get("record_time", "")).strip()
    poop_status = str(payload.get("poop_status", "")).strip()

    if not record_time_raw or not poop_status:
        return api_error("请提供 record_time 和 poop_status")

    if poop_status not in POOP_STATUS_OPTIONS:
        return api_error("poop_status 不支持，请使用：正常/奶瓣/酸臭")

    try:
        record_time = normalize_record_time(record_time_raw)
    except ValueError:
        return api_error("record_time 格式需为 YYYY-MM-DDTHH:MM")

    create_poop_record(record_time, poop_status)
    return api_ok({"message": "拉臭臭记录已保存"}, status=201)


@app.route("/api/v1/records/poop/<int:record_id>", methods=["DELETE"])
@require_unlock
def api_delete_poop_record(record_id: int):
    deleted = delete_poop_record(record_id)
    if not deleted:
        return api_error("拉臭臭记录不存在", status=404)
    return api_ok({"message": "拉臭臭记录已删除"})


@app.route("/api/v1/album/photos", methods=["GET"])
@require_unlock
def api_album_photos():
    photos = list_album_photos()
    return api_ok(
        {
            "data": photos,
            "meta": {
                "total": len(photos),
                "max_photos": app.config["ALBUM_MAX_PHOTOS"],
                "remaining": app.config["ALBUM_MAX_PHOTOS"] - len(photos),
            },
        }
    )


@app.route("/api/v1/album/photos", methods=["POST"])
@require_unlock
def api_album_upload_photos():
    files = request.files.getlist("photos")
    result = upload_album_photos(files)
    status = 201 if result["saved"] else 400
    return api_ok({"data": result}, status=status)


@app.route("/api/v1/album/photos/<int:photo_id>", methods=["DELETE"])
@require_unlock
def api_album_delete(photo_id: int):
    deleted = delete_album_photo(photo_id)
    if not deleted:
        return api_error("照片不存在", status=404)
    return api_ok({"message": "照片已删除"})


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    init_db()
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=False)
