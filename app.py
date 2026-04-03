import os
import sqlite3
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "yqlog.db"
UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "yqlog-dev-secret")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB per file


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS growth_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_date TEXT NOT NULL,
                height_cm REAL,
                weight_kg REAL,
                head_circumference_cm REAL,
                note TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                original_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(record_id) REFERENCES growth_records(id) ON DELETE CASCADE
            );
            """
        )


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def query_stats() -> Dict[str, Any]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, record_date, height_cm, weight_kg, head_circumference_cm
            FROM growth_records
            ORDER BY record_date ASC, id ASC
            """
        ).fetchall()

    if not rows:
        return {
            "total_records": 0,
            "latest_date": None,
            "avg_height": None,
            "avg_weight": None,
            "avg_head": None,
            "chart": [],
        }

    heights = [r["height_cm"] for r in rows if r["height_cm"] is not None]
    weights = [r["weight_kg"] for r in rows if r["weight_kg"] is not None]
    heads = [r["head_circumference_cm"] for r in rows if r["head_circumference_cm"] is not None]

    chart = [
        {
            "date": row["record_date"],
            "height": row["height_cm"],
            "weight": row["weight_kg"],
            "head": row["head_circumference_cm"],
        }
        for row in rows
    ]

    return {
        "total_records": len(rows),
        "latest_date": rows[-1]["record_date"],
        "avg_height": round(mean(heights), 2) if heights else None,
        "avg_weight": round(mean(weights), 2) if weights else None,
        "avg_head": round(mean(heads), 2) if heads else None,
        "chart": chart,
    }


def query_timeline() -> List[sqlite3.Row]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT r.id,
                   r.record_date,
                   r.height_cm,
                   r.weight_kg,
                   r.head_circumference_cm,
                   r.note,
                   r.created_at,
                   GROUP_CONCAT(p.file_name, ',') AS photo_files
            FROM growth_records r
            LEFT JOIN photos p ON p.record_id = r.id
            GROUP BY r.id
            ORDER BY r.record_date DESC, r.id DESC
            """
        ).fetchall()
    return rows


@app.route("/")
def index():
    stats = query_stats()
    timeline = query_timeline()[:6]
    return render_template("index.html", stats=stats, timeline=timeline)


@app.route("/timeline")
def timeline():
    records = query_timeline()
    return render_template("timeline.html", records=records)


@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        record_date = request.form.get("record_date", "").strip()
        height_cm = request.form.get("height_cm", "").strip()
        weight_kg = request.form.get("weight_kg", "").strip()
        head_cm = request.form.get("head_circumference_cm", "").strip()
        note = request.form.get("note", "").strip()

        if not record_date:
            flash("请填写记录日期", "error")
            return redirect(url_for("submit"))

        try:
            datetime.strptime(record_date, "%Y-%m-%d")
        except ValueError:
            flash("日期格式不正确，请使用 YYYY-MM-DD", "error")
            return redirect(url_for("submit"))

        def to_float(value: str):
            return float(value) if value else None

        try:
            height_val = to_float(height_cm)
            weight_val = to_float(weight_kg)
            head_val = to_float(head_cm)
        except ValueError:
            flash("身高/体重/头围请填写数字", "error")
            return redirect(url_for("submit"))

        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO growth_records (
                    record_date, height_cm, weight_kg, head_circumference_cm, note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (record_date, height_val, weight_val, head_val, note, now),
            )
            record_id = cursor.lastrowid

            files = request.files.getlist("photos")
            for file in files:
                if not file or not file.filename:
                    continue
                if not allowed_file(file.filename):
                    flash(f"文件 {file.filename} 格式不支持，已跳过", "warning")
                    continue

                safe_name = secure_filename(file.filename)
                unique_name = f"{record_id}_{int(datetime.utcnow().timestamp()*1000)}_{safe_name}"
                file.save(UPLOAD_DIR / unique_name)
                conn.execute(
                    """
                    INSERT INTO photos (record_id, file_name, original_name, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (record_id, unique_name, file.filename, now),
                )

        flash("成长记录已保存", "success")
        return redirect(url_for("timeline"))

    return render_template("submit.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)
