"""
Unit tests for ACEest Fitness & Gym Flask application (Aceestver-1.1).
Validates routes, response codes, and API responses.
"""

from urllib.parse import quote

import pytest
from app import app
from program_data import PROGRAMS


@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_returns_200(client):
    """Root returns OK and app info."""
    r = client.get("/")
    assert r.status_code == 200
    data = r.get_json()
    assert data is not None
    assert "app" in data
    assert "api" in data


def test_health_returns_ok(client):
    """Health check returns status ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json().get("status") == "ok"


def test_api_programs_returns_list(client):
    """GET /api/programs returns list of program names."""
    r = client.get("/api/programs")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert set(data) == set(PROGRAMS.keys())


def test_api_program_valid_returns_200(client):
    """GET /api/program/<name> returns 200 and workout/diet/color/calorie_factor."""
    for name in PROGRAMS:
        r = client.get(f"/api/program/{quote(name)}")
        assert r.status_code == 200, f"Failed for program: {name}"
        data = r.get_json()
        assert "workout" in data
        assert "diet" in data
        assert "color" in data
        assert "calorie_factor" in data


def test_api_program_fat_loss_content(client):
    """Fat Loss program contains expected content."""
    r = client.get(f"/api/program/{quote('Fat Loss (FL)')}")
    assert r.status_code == 200
    data = r.get_json()
    assert "Back Squat" in data["workout"]
    assert "2000" in data["diet"]
    assert data["calorie_factor"] == 22


def test_api_program_muscle_gain_content(client):
    """Muscle Gain program contains expected content."""
    r = client.get(f"/api/program/{quote('Muscle Gain (MG)')}")
    assert r.status_code == 200
    data = r.get_json()
    assert "Squat" in data["workout"]
    assert "3200" in data["diet"]
    assert data["calorie_factor"] == 35


def test_api_program_beginner_content(client):
    """Beginner program contains expected content."""
    r = client.get(f"/api/program/{quote('Beginner (BG)')}")
    assert r.status_code == 200
    data = r.get_json()
    assert "Full Body Circuit" in data["workout"]
    assert "120g/day" in data["diet"]
    assert data["calorie_factor"] == 26


def test_api_program_invalid_returns_404(client):
    """GET /api/program/<unknown> returns 404."""
    r = client.get("/api/program/UnknownProgram")
    assert r.status_code == 404
    assert "error" in r.get_json()
