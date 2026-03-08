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
            weight REAL,
            program TEXT,
            calories INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            week TEXT,
            adherence INTEGER
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


@app.route("/api/clients", methods=["GET"])
def list_clients():
    """Return all clients."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, name, age, weight, program, calories FROM clients")
    rows = cur.fetchall()
    clients = [
        {"id": r["id"], "name": r["name"], "age": r["age"], "weight": r["weight"], "program": r["program"], "calories": r["calories"]}
        for r in rows
    ]
    return jsonify(clients)


@app.route("/api/clients/<path:name>", methods=["GET"])
def get_client(name):
    """Return one client by name."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, name, age, weight, program, calories FROM clients WHERE name = ?", (name,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(dict(row))


@app.route("/api/clients", methods=["POST"])
def create_client():
    """Create or replace a client. JSON: name, age, weight, program, calories."""
    data = request.get_json() or {}
    if not data.get("name") or not data.get("program"):
        return jsonify({"error": "name and program required"}), 400
    name = str(data["name"])
    age = int(data.get("age", 0))
    weight = float(data.get("weight", 0))
    program = str(data["program"])
    calories = int(data.get("calories", 0))
    if calories <= 0 and program in PROGRAMS:
        calories = int(weight * PROGRAMS[program].get("calorie_factor", 0))
    db = get_db()
    try:
        db.cursor().execute(
            "INSERT OR REPLACE INTO clients (name, age, weight, program, calories) VALUES (?, ?, ?, ?, ?)",
            (name, age, weight, program, calories),
        )
        db.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    cur = db.cursor()
    cur.execute("SELECT id, name, age, weight, program, calories FROM clients WHERE name = ?", (name,))
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
