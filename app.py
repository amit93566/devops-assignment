"""
ACEest Fitness & Gym - Flask backend (API).
Service endpoints for program data; consumed by Tkinter frontend (Aceestver-1.0).
"""

from flask import Flask, jsonify

from program_data import PROGRAMS

app = Flask(__name__)


@app.route("/")
def index():
    """Root: minimal info and link to API."""
    return jsonify(
        {
            "app": "ACEest Fitness & Gym",
            "api": {
                "programs": "/api/programs",
                "program": "/api/program/<name>",
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
    """Return workout and diet for a program by name."""
    if name not in PROGRAMS:
        return jsonify({"error": "Program not found"}), 404
    return jsonify(PROGRAMS[name])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
