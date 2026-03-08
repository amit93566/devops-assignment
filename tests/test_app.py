"""
Unit tests for ACEest Fitness & Gym Flask application (Aceestver-1.1.2).
Validates routes, response codes, and API responses.
"""

from urllib.parse import quote

import pytest
from app import app, CLIENTS
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
    assert "app" in data and "api" in data


def test_health_returns_ok(client):
    """Health check returns status ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json().get("status") == "ok"


def test_api_programs_returns_list(client):
    """GET /api/programs returns list of program names."""
    r = client.get("/api/programs")
    assert r.status_code == 200
    assert set(r.get_json()) == set(PROGRAMS.keys())


def test_api_program_valid_returns_200(client):
    """GET /api/program/<name> returns 200 and workout/diet/color/calorie_factor."""
    for name in PROGRAMS:
        r = client.get(f"/api/program/{quote(name)}")
        assert r.status_code == 200
        data = r.get_json()
        assert "workout" in data and "diet" in data and "color" in data and "calorie_factor" in data


def test_api_program_fat_loss_content(client):
    """Fat Loss program contains expected content."""
    r = client.get(f"/api/program/{quote('Fat Loss (FL)')}")
    assert r.status_code == 200
    data = r.get_json()
    assert "Back Squat" in data["workout"]
    assert "Egg Whites" in data["diet"]
    assert data["calorie_factor"] == 22


def test_api_program_muscle_gain_content(client):
    """Muscle Gain program contains expected content."""
    r = client.get(f"/api/program/{quote('Muscle Gain (MG)')}")
    assert r.status_code == 200
    data = r.get_json()
    assert "Squat" in data["workout"]
    assert "Biryani" in data["diet"]
    assert data["calorie_factor"] == 35


def test_api_program_beginner_content(client):
    """Beginner program contains expected content."""
    r = client.get(f"/api/program/{quote('Beginner (BG)')}")
    assert r.status_code == 200
    data = r.get_json()
    assert "Air Squats" in data["workout"]
    assert "Tamil Meals" in data["diet"]
    assert data["calorie_factor"] == 26


def test_api_program_invalid_returns_404(client):
    """GET /api/program/<unknown> returns 404."""
    r = client.get("/api/program/UnknownProgram")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_api_clients_list_empty(client):
    """GET /api/clients returns list (may be empty)."""
    CLIENTS.clear()
    r = client.get("/api/clients")
    assert r.status_code == 200
    assert r.get_json() == []


def test_api_clients_post_and_list(client):
    """POST /api/clients creates client; GET returns it."""
    CLIENTS.clear()
    r = client.post(
        "/api/clients",
        json={"name": "Test", "program": "Beginner (BG)", "age": 25, "weight": 70, "adherence": 80, "notes": "OK"},
        content_type="application/json",
    )
    assert r.status_code == 201
    assert r.get_json()["name"] == "Test"
    r2 = client.get("/api/clients")
    assert r2.status_code == 200
    assert len(r2.get_json()) == 1
    assert r2.get_json()[0]["name"] == "Test"
    CLIENTS.clear()


def test_api_clients_post_requires_name_and_program(client):
    """POST /api/clients without name or program returns 400."""
    r = client.post("/api/clients", json={}, content_type="application/json")
    assert r.status_code == 400
