"""
ACEest Fitness & Gym - Flask backend (API).
Program data + SQLite for clients and progress. Consumed by Tkinter frontend.
"""

import os
import sqlite3

from flask import Flask, g, jsonify, request

from program_data import PROGRAMS

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("DATABASE", "aceest_fitness.db")


def get_db():
    """Get a DB connection and ensure tables exist."""
    db_path = app.config["DATABASE"]
    if db_path == ":memory:":
        if not getattr(app, "_db", None):
            app._db = sqlite3.connect(":memory:", check_same_thread=False)
            app._db.row_factory = sqlite3.Row
            _init_tables(app._db)
        return app._db
    if "db" not in g:
        g.db = sqlite3.connect(db_path, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        _init_tables(g.db)
    return g.db


def _init_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            age INTEGER,
            height REAL,
            weight REAL,
            program TEXT,
            calories INTEGER,
            target_weight REAL,
            target_adherence INTEGER
        )
    """)
    # Migrate old schema: add columns if missing
    cur.execute("PRAGMA table_info(clients)")
    cols = {row[1] for row in cur.fetchall()}
    if "height" not in cols:
        cur.execute("ALTER TABLE clients ADD COLUMN height REAL")
    if "target_weight" not in cols:
        cur.execute("ALTER TABLE clients ADD COLUMN target_weight REAL")
    if "target_adherence" not in cols:
        cur.execute("ALTER TABLE clients ADD COLUMN target_adherence INTEGER")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            week TEXT,
            adherence INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            date TEXT,
            workout_type TEXT,
            duration_min INTEGER,
            notes TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER,
            name TEXT,
            sets INTEGER,
            reps INTEGER,
            weight REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            date TEXT,
            weight REAL,
            waist REAL,
            bodyfat REAL
        )
    """)
    conn.commit()


@app.teardown_appcontext
def close_db(exception=None):
    if "db" in g:
        g.db.close()


@app.route("/")
def index():
    """Root: minimal info and link to API."""
    return jsonify(
        {
            "app": "ACEest Fitness & Gym",
            "api": {
                "programs": "/api/programs",
                "program": "/api/program/<name>",
                "clients": "/api/clients",
                "client_by_name": "/api/clients/<name>",
                "progress": "/api/progress",
                "progress_by_client": "/api/progress/<name>",
                "metrics_by_client": "/api/metrics/<name>",
                "workouts_by_client": "/api/workouts/<name>",
            },
            "health": "/health",
        }
    )


@app.route("/health")
def health():
    """Health check for CI/CD and load balancers."""
    return jsonify({"status": "ok"})


@app.route("/api/programs")
def list_programs():
    """Return list of program names."""
    return jsonify(list(PROGRAMS.keys()))


@app.route("/api/program/<path:name>")
def get_program(name):
    """Return workout, diet, color, calorie_factor for a program by name."""
    if name not in PROGRAMS:
        return jsonify({"error": "Program not found"}), 404
    return jsonify(PROGRAMS[name])


CLIENT_COLS = "id, name, age, height, weight, program, calories, target_weight, target_adherence"


@app.route("/api/clients", methods=["GET"])
def list_clients():
    """Return all clients."""
    db = get_db()
    cur = db.cursor()
    cur.execute(f"SELECT {CLIENT_COLS} FROM clients ORDER BY name")
    rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/clients/<path:name>", methods=["GET"])
def get_client(name):
    """Return one client by name."""
    db = get_db()
    cur = db.cursor()
    cur.execute(f"SELECT {CLIENT_COLS} FROM clients WHERE name = ?", (name,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(dict(row))


@app.route("/api/clients", methods=["POST"])
def create_client():
    """Create or replace a client. JSON: name, age, height, weight, program, calories, target_weight, target_adherence."""
    data = request.get_json() or {}
    if not data.get("name") or not data.get("program"):
        return jsonify({"error": "name and program required"}), 400
    name = str(data["name"]).strip()
    age = data.get("age")
    age = int(age) if age is not None else None
    height = data.get("height")
    height = float(height) if height is not None else None
    weight = data.get("weight")
    weight = float(weight) if weight is not None else None
    program = str(data["program"])
    calories = data.get("calories")
    calories = int(calories) if calories is not None else None
    if (calories is None or calories <= 0) and program in PROGRAMS and weight:
        calories = int(weight * PROGRAMS[program].get("calorie_factor", 0))
    target_weight = data.get("target_weight")
    target_weight = float(target_weight) if target_weight is not None else None
    target_adherence = data.get("target_adherence")
    target_adherence = int(target_adherence) if target_adherence is not None else None
    db = get_db()
    try:
        db.cursor().execute(
            """INSERT OR REPLACE INTO clients
               (name, age, height, weight, program, calories, target_weight, target_adherence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, age, height, weight, program, calories or 0, target_weight, target_adherence),
        )
        db.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    cur = db.cursor()
    cur.execute(f"SELECT {CLIENT_COLS} FROM clients WHERE name = ?", (name,))
    row = cur.fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/progress", methods=["POST"])
def save_progress():
    """Save progress. JSON: client_name, week, adherence."""
    data = request.get_json() or {}
    if not data.get("client_name"):
        return jsonify({"error": "client_name required"}), 400
    client_name = str(data["client_name"])
    week = str(data.get("week", ""))
    adherence = int(data.get("adherence", 0))
    db = get_db()
    try:
        db.cursor().execute(
            "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
            (client_name, week, adherence),
        )
        db.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "saved", "client_name": client_name, "week": week, "adherence": adherence}), 201


@app.route("/api/progress/<path:client_name>", methods=["GET"])
def get_progress(client_name):
    """Return progress entries for a client (week, adherence) ordered by id."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT week, adherence FROM progress WHERE client_name = ? ORDER BY id",
        (client_name,),
    )
    rows = cur.fetchall()
    data = [{"week": r["week"], "adherence": r["adherence"]} for r in rows]
    return jsonify(data)


@app.route("/api/metrics/<path:client_name>", methods=["GET"])
def get_metrics(client_name):
    """Return metrics for a client (date, weight, waist, bodyfat) ordered by date."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT date, weight, waist, bodyfat FROM metrics WHERE client_name = ? ORDER BY date",
        (client_name,),
    )
    rows = cur.fetchall()
    data = [{"date": r["date"], "weight": r["weight"], "waist": r["waist"], "bodyfat": r["bodyfat"]} for r in rows]
    return jsonify(data)


@app.route("/api/metrics", methods=["POST"])
def save_metrics():
    """Save body metrics. JSON: client_name, date, weight, waist, bodyfat."""
    data = request.get_json() or {}
    if not data.get("client_name"):
        return jsonify({"error": "client_name required"}), 400
    client_name = str(data["client_name"])
    m_date = str(data.get("date", ""))
    weight = data.get("weight") is not None and float(data["weight"]) or None
    waist = data.get("waist") is not None and float(data["waist"]) or None
    bodyfat = data.get("bodyfat") is not None and float(data["bodyfat"]) or None
    db = get_db()
    try:
        db.cursor().execute(
            "INSERT INTO metrics (client_name, date, weight, waist, bodyfat) VALUES (?, ?, ?, ?, ?)",
            (client_name, m_date, weight, waist, bodyfat),
        )
        db.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "saved", "client_name": client_name, "date": m_date}), 201


@app.route("/api/workouts/<path:client_name>", methods=["GET"])
def get_workouts(client_name):
    """Return workouts for a client (date, workout_type, duration_min, notes) ordered by date desc."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT date, workout_type, duration_min, notes FROM workouts WHERE client_name = ? ORDER BY date DESC, id DESC",
        (client_name,),
    )
    rows = cur.fetchall()
    data = [
        {"date": r["date"], "workout_type": r["workout_type"], "duration_min": r["duration_min"], "notes": r["notes"] or ""}
        for r in rows
    ]
    return jsonify(data)


@app.route("/api/workouts", methods=["POST"])
def save_workout():
    """Save a workout. JSON: client_name, date, workout_type, duration_min, notes, exercises (optional list)."""
    data = request.get_json() or {}
    if not data.get("client_name"):
        return jsonify({"error": "client_name required"}), 400
    if not data.get("date") or not data.get("workout_type"):
        return jsonify({"error": "date and workout_type required"}), 400
    client_name = str(data["client_name"])
    w_date = str(data["date"])
    workout_type = str(data.get("workout_type", ""))
    duration_min = int(data.get("duration_min", 0))
    notes = str(data.get("notes", ""))
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute(
            "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?, ?, ?, ?, ?)",
            (client_name, w_date, workout_type, duration_min, notes),
        )
        workout_id = cur.lastrowid
        for ex in data.get("exercises") or []:
            cur.execute(
                "INSERT INTO exercises (workout_id, name, sets, reps, weight) VALUES (?, ?, ?, ?, ?)",
                (
                    workout_id,
                    str(ex.get("name", "")),
                    int(ex.get("sets", 0)),
                    int(ex.get("reps", 0)),
                    float(ex.get("weight", 0)),
                ),
            )
        db.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "saved", "client_name": client_name, "workout_id": workout_id}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
