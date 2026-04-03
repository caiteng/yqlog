import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.permanent_session_lifetime = timedelta(days=app.config["SESSION_DAYS"])


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
            WHERE DATE(record_time) >= DATE('now', '-29 day')
            GROUP BY DATE(record_time)
            ORDER BY day ASC
            """
        ).fetchall()

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
            WHERE DATE(record_time) >= DATE('now', '-29 day')
            GROUP BY DATE(record_time)
            ORDER BY day ASC
            """
        ).fetchall()

        poop_status = conn.execute(
            """
            SELECT poop_status,
                   COUNT(*) AS count
            FROM poop_records
            WHERE DATE(record_time) >= DATE('now', '-29 day')
            GROUP BY poop_status
            """
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


def query_timeline() -> List[Dict[str, str]]:
    events: List[Dict[str, str]] = []

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
                "time": row["record_time"],
                "type": "喝奶",
                "detail": f"喝奶 {row['milk_ml']} ML",
            }
        )

    for row in poop_rows:
        events.append(
            {
                "time": row["record_time"],
                "type": "拉臭臭",
                "detail": f"状态：{row['poop_status']}",
            }
        )

    events.sort(key=lambda item: item["time"], reverse=True)
    return events[:100]


@app.route("/")
def index():
    dashboard = query_dashboard()
    return render_template("index.html", dashboard=dashboard)


@app.route("/timeline")
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

        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO milk_records (record_time, milk_ml, created_at) VALUES (?, ?, ?)",
                (record_time, milk_ml, now),
            )

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

        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO poop_records (record_time, poop_status, created_at) VALUES (?, ?, ?)",
                (record_time, poop_status, now),
            )

        flash("拉臭臭记录已保存", "success")
        return redirect(url_for("quick_entry"))

    return render_template("poop.html", default_time=record_time_input_default())


@app.route("/album")
@require_unlock
def album():
    with get_conn() as conn:
        photos = conn.execute(
            """
            SELECT id, image_path, created_at
            FROM album_photos
            ORDER BY created_at DESC
            """
        ).fetchall()
    return render_template("album.html", photos=photos)


@app.route("/album/upload", methods=["POST"])
@require_unlock
def album_upload():
    files = request.files.getlist("photos")
    if not files:
        flash("请选择要上传的照片", "warning")
        return redirect(url_for("album"))

    now = datetime.utcnow().isoformat()
    saved = 0

    with get_conn() as conn:
        for file in files:
            if not file or not file.filename:
                continue
            if not allowed_file(file.filename):
                flash(f"文件 {file.filename} 格式不支持，已跳过", "warning")
                continue

            safe_name = secure_filename(file.filename)
            unique_name = f"album_{int(datetime.utcnow().timestamp() * 1000)}_{safe_name}"
            file.save(app.config["UPLOAD_FOLDER"] / unique_name)
            conn.execute(
                "INSERT INTO album_photos (image_path, created_at) VALUES (?, ?)",
                (unique_name, now),
            )
            saved += 1

    if saved:
        flash(f"已上传 {saved} 张照片", "success")
    return redirect(url_for("album"))


@app.route("/album/delete/<int:photo_id>", methods=["POST"])
@require_unlock
def album_delete(photo_id: int):
    with get_conn() as conn:
        photo = conn.execute(
            "SELECT id, image_path FROM album_photos WHERE id = ?",
            (photo_id,),
        ).fetchone()

        if not photo:
            flash("照片不存在", "warning")
            return redirect(url_for("album"))

        conn.execute("DELETE FROM album_photos WHERE id = ?", (photo_id,))

    file_path = app.config["UPLOAD_FOLDER"] / photo["image_path"]
    if file_path.exists():
        file_path.unlink()

    flash("照片已删除", "success")
    return redirect(url_for("album"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=False)
