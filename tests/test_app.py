"""
Unit tests for ACEest Fitness & Gym Flask application.
Validates program routes, client API, and progress API (SQLite in app.py).
"""

from urllib.parse import quote

import pytest
from app import app
from program_data import PROGRAMS


@pytest.fixture
def client():
    """Flask test client with in-memory SQLite."""
    app.config["TESTING"] = True
    app.config["DATABASE"] = ":memory:"
    if hasattr(app, "_db"):
        del app._db
    with app.test_client() as c:
        yield c


def test_index_returns_200(client):
    """Root returns OK and app info."""
    r = client.get("/")
    assert r.status_code == 200
    data = r.get_json()
    assert "app" in data and "api" in data
    assert "clients" in data["api"]


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
    """GET /api/program/<name> returns 200 and workout/diet/color/calorie_factor/desc."""
    for name in PROGRAMS:
        r = client.get(f"/api/program/{quote(name)}")
        assert r.status_code == 200
        data = r.get_json()
        assert "workout" in data and "diet" in data and "color" in data and "calorie_factor" in data and "desc" in data


def test_api_program_fat_loss_content(client):
    """Fat Loss 3-day program contains expected content."""
    r = client.get(f"/api/program/{quote('Fat Loss (FL) – 3 day')}")
    assert r.status_code == 200
    data = r.get_json()
    assert "Back Squat" in data["workout"]
    assert data["calorie_factor"] == 22


def test_api_program_muscle_gain_content(client):
    """Muscle Gain PPL program contains expected content."""
    name = next(k for k in PROGRAMS if "Muscle Gain" in k and "PPL" in k)
    r = client.get(f"/api/program/{quote(name)}")
    assert r.status_code == 200
    data = r.get_json()
    assert "Squat" in data["workout"]
    assert data["calorie_factor"] == 35


def test_api_program_beginner_content(client):
    """Beginner program contains expected content."""
    r = client.get(f"/api/program/{quote('Beginner (BG)')}")
    assert r.status_code == 200
    data = r.get_json()
    assert "Air Squats" in data["workout"]
    assert data["calorie_factor"] == 26


def test_api_program_invalid_returns_404(client):
    """GET /api/program/<unknown> returns 404."""
    r = client.get("/api/program/UnknownProgram")
    assert r.status_code == 404
    assert "error" in r.get_json()


# ---------- Client API (SQLite in app.py) ----------


def test_api_clients_list_empty(client):
    """GET /api/clients returns empty list when no clients."""
    r = client.get("/api/clients")
    assert r.status_code == 200
    assert r.get_json() == []


def test_api_clients_post_creates_client(client):
    """POST /api/clients creates a client and returns 201."""
    r = client.post(
        "/api/clients",
        json={
            "name": "Test User",
            "age": 30,
            "weight": 70.0,
            "program": "Beginner (BG)",
            "calories": 1820,
        },
        content_type="application/json",
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data["name"] == "Test User"
    assert data["program"] == "Beginner (BG)"
    assert data["calories"] == 1820
    assert "height" in data and "target_weight" in data and "target_adherence" in data and "membership_expiry" in data


def test_api_clients_list_after_post(client):
    """GET /api/clients returns saved client."""
    client.post(
        "/api/clients",
        json={"name": "Alice", "program": "Fat Loss (FL) – 3 day", "age": 25, "weight": 60, "calories": 1320},
        content_type="application/json",
    )
    r = client.get("/api/clients")
    assert r.status_code == 200
    lst = r.get_json()
    assert len(lst) == 1
    assert lst[0]["name"] == "Alice"
    assert lst[0]["calories"] == 1320


def test_api_clients_get_by_name(client):
    """GET /api/clients/<name> returns client."""
    client.post(
        "/api/clients",
        json={"name": "Bob", "program": "Muscle Gain (MG) – PPL", "age": 28, "weight": 80, "calories": 2800},
        content_type="application/json",
    )
    r = client.get("/api/clients/Bob")
    assert r.status_code == 200
    data = r.get_json()
    assert data["name"] == "Bob"
    assert data["program"] == "Muscle Gain (MG) – PPL"


def test_api_clients_get_by_name_404(client):
    """GET /api/clients/<name> returns 404 when not found."""
    r = client.get("/api/clients/NoSuchClient")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_api_clients_post_requires_name_and_program(client):
    """POST /api/clients without name or program returns 400."""
    r = client.post("/api/clients", json={}, content_type="application/json")
    assert r.status_code == 400
    r2 = client.post("/api/clients", json={"name": "X"}, content_type="application/json")
    assert r2.status_code == 400


def test_api_login_success(client):
    """POST /api/login with admin/admin returns 200 and username, role."""
    r = client.post(
        "/api/login",
        json={"username": "admin", "password": "admin"},
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data.get("username") == "admin"
    assert data.get("role") == "Admin"


def test_api_login_failure(client):
    """POST /api/login with wrong credentials returns 401."""
    r = client.post(
        "/api/login",
        json={"username": "admin", "password": "wrong"},
        content_type="application/json",
    )
    assert r.status_code == 401
    assert "error" in r.get_json()


def test_api_login_requires_username_password(client):
    """POST /api/login without username or password returns 400."""
    r = client.post("/api/login", json={}, content_type="application/json")
    assert r.status_code == 400


def test_api_progress_post(client):
    """POST /api/progress saves progress and returns 201."""
    client.post(
        "/api/clients",
        json={"name": "Jane", "program": "Beginner (BG)", "age": 22, "weight": 55, "calories": 1430},
        content_type="application/json",
    )
    r = client.post(
        "/api/progress",
        json={"client_name": "Jane", "week": "Week 10 - 2025", "adherence": 85},
        content_type="application/json",
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data.get("status") == "saved"
    assert data.get("client_name") == "Jane"
    assert data.get("adherence") == 85


def test_api_progress_post_requires_client_name(client):
    """POST /api/progress without client_name returns 400."""
    r = client.post("/api/progress", json={"week": "Week 1", "adherence": 50}, content_type="application/json")
    assert r.status_code == 400


def test_api_progress_get_by_client_empty(client):
    """GET /api/progress/<client_name> returns empty list when no progress."""
    r = client.get("/api/progress/SomeClient")
    assert r.status_code == 200
    assert r.get_json() == []


def test_api_progress_get_by_client(client):
    """GET /api/progress/<client_name> returns list of week, adherence."""
    client.post(
        "/api/clients",
        json={"name": "ChartUser", "program": "Beginner (BG)", "age": 25, "weight": 70, "calories": 1820},
        content_type="application/json",
    )
    client.post(
        "/api/progress",
        json={"client_name": "ChartUser", "week": "Week 01 - 2025", "adherence": 80},
        content_type="application/json",
    )
    client.post(
        "/api/progress",
        json={"client_name": "ChartUser", "week": "Week 02 - 2025", "adherence": 90},
        content_type="application/json",
    )
    r = client.get("/api/progress/ChartUser")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 2
    assert data[0]["week"] == "Week 01 - 2025" and data[0]["adherence"] == 80
    assert data[1]["week"] == "Week 02 - 2025" and data[1]["adherence"] == 90


# ---------- Metrics API ----------


def test_api_metrics_get_empty(client):
    """GET /api/metrics/<client_name> returns empty list when no metrics."""
    r = client.get("/api/metrics/AnyClient")
    assert r.status_code == 200
    assert r.get_json() == []


def test_api_metrics_post_and_get(client):
    """POST /api/metrics saves; GET returns list."""
    client.post(
        "/api/clients",
        json={"name": "M", "program": "Beginner (BG)", "age": 30, "weight": 70},
        content_type="application/json",
    )
    r = client.post(
        "/api/metrics",
        json={"client_name": "M", "date": "2025-03-01", "weight": 70.5, "waist": 80, "bodyfat": 18},
        content_type="application/json",
    )
    assert r.status_code == 201
    r2 = client.get("/api/metrics/M")
    assert r2.status_code == 200
    data = r2.get_json()
    assert len(data) == 1
    assert data[0]["date"] == "2025-03-01" and data[0]["weight"] == 70.5


# ---------- Workouts API ----------


def test_api_workouts_get_empty(client):
    """GET /api/workouts/<client_name> returns empty list when no workouts."""
    r = client.get("/api/workouts/AnyClient")
    assert r.status_code == 200
    assert r.get_json() == []


def test_api_workouts_post_and_get(client):
    """POST /api/workouts saves; GET returns list."""
    client.post(
        "/api/clients",
        json={"name": "W", "program": "Beginner (BG)", "age": 28},
        content_type="application/json",
    )
    r = client.post(
        "/api/workouts",
        json={
            "client_name": "W",
            "date": "2025-03-05",
            "workout_type": "Strength",
            "duration_min": 60,
            "notes": "Heavy day",
        },
        content_type="application/json",
    )
    assert r.status_code == 201
    r2 = client.get("/api/workouts/W")
    assert r2.status_code == 200
    data = r2.get_json()
    assert len(data) == 1
    assert data[0]["date"] == "2025-03-05" and data[0]["workout_type"] == "Strength"
