"""
ACEest Fitness & Gym - Flask backend (API).
Service endpoints for program and client data; consumed by Tkinter frontend (Aceestver-1.1.2).
"""

from flask import Flask, jsonify, request

from program_data import PROGRAMS

app = Flask(__name__)

CLIENTS = []


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
    return jsonify(CLIENTS)


@app.route("/api/clients", methods=["POST"])
def create_client():
    """Save a client. Expects JSON: name, age, weight, program, adherence, notes."""
    data = request.get_json() or {}
    if not data.get("name") or not data.get("program"):
        return jsonify({"error": "name and program required"}), 400
    client = {
        "name": str(data.get("name", "")),
        "age": int(data.get("age", 0)),
        "weight": float(data.get("weight", 0)),
        "program": str(data.get("program", "")),
        "adherence": int(data.get("adherence", 0)),
        "notes": str(data.get("notes", "")),
    }
    CLIENTS.append(client)
    return jsonify(client), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
