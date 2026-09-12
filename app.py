import calendar
import os
import sqlite3
from datetime import date, timedelta

from flask import Flask, g, jsonify, redirect, render_template, request, url_for

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "data", "fitness.db"))
PERSON_A_NAME = os.environ.get("PERSON_A_NAME", "user1")
PERSON_B_NAME = os.environ.get("PERSON_B_NAME", "user2")
VALID_PERSONS = {"a", "b"}

STREAK_TIERS = [
    (30, "epic"),
    (7, "hot"),
    (3, "warm"),
    (0, "cold"),
]

app = Flask(__name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT NOT NULL CHECK (person IN ('a', 'b')),
            entry_date TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_entries_date ON entries (entry_date)")
    db.commit()
    db.close()


@app.context_processor
def inject_person_names():
    return {"person_a_name": PERSON_A_NAME, "person_b_name": PERSON_B_NAME}


def get_entry_dates(db, person):
    rows = db.execute("SELECT DISTINCT entry_date FROM entries WHERE person = ?", (person,)).fetchall()
    return {row["entry_date"] for row in rows}


def streak_tier(length):
    for threshold, name in STREAK_TIERS:
        if length >= threshold:
            return name
    return "cold"


def compute_streak(dates, today):
    cursor = today if today.isoformat() in dates else today - timedelta(days=1)
    length = 0
    d = cursor
    while d.isoformat() in dates:
        length += 1
        d -= timedelta(days=1)
    start = cursor - timedelta(days=length - 1) if length else None
    end = cursor if length else None
    return {"length": length, "tier": streak_tier(length), "start": start, "end": end}


def month_days_iso(year, month):
    _, days_in_month = calendar.monthrange(year, month)
    return [date(year, month, d).isoformat() for d in range(1, days_in_month + 1)]


def is_month_complete(dates, year, month, today):
    if (year, month) >= (today.year, today.month):
        return False
    return all(d in dates for d in month_days_iso(year, month))


def completed_months(dates, today):
    months = sorted({d[:7] for d in dates})
    result = []
    for ym in months:
        y, m = int(ym[:4]), int(ym[5:7])
        if is_month_complete(dates, y, m, today):
            result.append((y, m))
    return result


def week_bounds(d):
    monday = d - timedelta(days=d.weekday())
    return monday, monday + timedelta(days=6)


def is_week_complete(dates, monday):
    return all((monday + timedelta(days=i)).isoformat() in dates for i in range(7))


def completed_team_weeks(dates_a, dates_b, today, range_start, range_end):
    current_week_monday, _ = week_bounds(today)
    monday, _ = week_bounds(range_start)
    result = []
    while monday <= range_end:
        if monday < current_week_monday and is_week_complete(dates_a, monday) and is_week_complete(dates_b, monday):
            result.append(monday)
        monday += timedelta(days=7)
    return result


MONTH_NAMES = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def build_badges(dates_a, dates_b, today, range_start, range_end):
    badges = []
    for y, m in completed_months(dates_a, today):
        badges.append({"icon": "🏆", "label": f"{PERSON_A_NAME} – {MONTH_NAMES[m - 1]} {y}", "sort_key": date(y, m, 1)})
    for y, m in completed_months(dates_b, today):
        badges.append({"icon": "🏆", "label": f"{PERSON_B_NAME} – {MONTH_NAMES[m - 1]} {y}", "sort_key": date(y, m, 1)})
    for monday in completed_team_weeks(dates_a, dates_b, today, range_start, range_end):
        sunday = monday + timedelta(days=6)
        label = f"Team-Woche {monday.strftime('%d.%m.')} – {sunday.strftime('%d.%m.%Y')}"
        badges.append({"icon": "❤️", "label": label, "sort_key": monday})
    badges.sort(key=lambda b: b["sort_key"], reverse=True)
    return badges


@app.route("/")
def index():
    today = date.today()
    return redirect(url_for("calendar_view", year=today.year, month=today.month))


@app.route("/calendar/<int:year>/<int:month>")
def calendar_view(year, month):
    if month < 1 or month > 12:
        return redirect(url_for("index"))

    _, days_in_month = calendar.monthrange(year, month)
    month_start = f"{year:04d}-{month:02d}-01"
    month_end = f"{year:04d}-{month:02d}-{days_in_month:02d}"

    db = get_db()
    rows = db.execute(
        "SELECT id, person, entry_date, text FROM entries "
        "WHERE entry_date BETWEEN ? AND ? ORDER BY id",
        (month_start, month_end),
    ).fetchall()

    entries_by_day = {}
    for row in rows:
        day = int(row["entry_date"][-2:])
        entries_by_day.setdefault(day, {"a": [], "b": []})[row["person"]].append(
            {"id": row["id"], "text": row["text"]}
        )

    today = date.today()

    dates_a = get_entry_dates(db, "a")
    dates_b = get_entry_dates(db, "b")
    streak_a = compute_streak(dates_a, today)
    streak_b = compute_streak(dates_b, today)
    month_complete_a = is_month_complete(dates_a, year, month, today)
    month_complete_b = is_month_complete(dates_b, year, month, today)

    range_start = date(year, month, 1)
    range_end = date(year, month, days_in_month)
    team_week_mondays = completed_team_weeks(dates_a, dates_b, today, range_start, range_end)
    team_week_days = set()
    for monday in team_week_mondays:
        for i in range(7):
            team_week_days.add((monday + timedelta(days=i)).isoformat())

    badges = build_badges(dates_a, dates_b, today, range_start, range_end)

    day_rows = []
    for day in range(1, days_in_month + 1):
        current = date(year, month, day)
        in_streak_a = streak_a["start"] is not None and streak_a["start"] <= current <= streak_a["end"]
        in_streak_b = streak_b["start"] is not None and streak_b["start"] <= current <= streak_b["end"]
        day_rows.append(
            {
                "day": day,
                "date_iso": current.isoformat(),
                "weekday_name": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][current.weekday()],
                "is_weekend": current.weekday() >= 5,
                "is_today": current == today,
                "entries_a": entries_by_day.get(day, {"a": [], "b": []})["a"],
                "entries_b": entries_by_day.get(day, {"a": [], "b": []})["b"],
                "in_streak_a": in_streak_a,
                "in_streak_b": in_streak_b,
                "team_week": current.isoformat() in team_week_days,
            }
        )

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        month_name=MONTH_NAMES[month - 1],
        day_rows=day_rows,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        today_year=today.year,
        today_month=today.month,
        streak_a=streak_a,
        streak_b=streak_b,
        month_complete_a=month_complete_a,
        month_complete_b=month_complete_b,
        badges=badges,
    )


@app.route("/entries", methods=["POST"])
def add_entry():
    payload = request.get_json(silent=True) or {}
    person = payload.get("person")
    entry_date = payload.get("date")
    text = (payload.get("text") or "").strip()

    if person not in VALID_PERSONS:
        return jsonify({"error": "invalid person"}), 400
    if not text:
        return jsonify({"error": "text must not be empty"}), 400
    try:
        date.fromisoformat(entry_date)
    except (TypeError, ValueError):
        return jsonify({"error": "invalid date"}), 400

    db = get_db()
    cursor = db.execute(
        "INSERT INTO entries (person, entry_date, text) VALUES (?, ?, ?)",
        (person, entry_date, text),
    )
    db.commit()
    return jsonify({"id": cursor.lastrowid, "text": text, "person": person, "date": entry_date}), 201


@app.route("/entries/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    db = get_db()
    db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    db.commit()
    return "", 204


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
