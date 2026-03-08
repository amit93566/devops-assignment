# ACEest Fitness & Gym

Flask backend API plus Tkinter desktop frontend for fitness and gym management. Program data (Fat Loss, Muscle Gain, Beginner) is served by the Flask API and consumed by the Tkinter GUI or any HTTP client. Includes CI/CD via GitHub Actions and Jenkins BUILD.

---

## Architecture

- **Backend (Flask)** – `app.py` exposes REST endpoints: **POST /api/login** (username, password → role); `/api/programs`, `/api/program/<name>`, `/api/clients` (GET/POST), `/api/clients/<name>` (GET), plus progress, metrics, workouts. DB: `aceest_fitness.db` (**users** with default admin/admin; clients with **membership_expiry**; progress; workouts; exercises; metrics). Runs in Docker and in CI.
- **Frontend (Tkinter)** – `gui.py` (Aceestver-3.1.2): **Login** first (admin/admin); then **ACEest Fitness Dashboard** with **Select Client**, Client Management (name, age, height, weight, program, **Membership Expiry**), **Save Client**, **Load Client**, **Generate AI Program** (experience → random weekly plan in Treeview), **Export PDF Report** (fpdf2). Right panel: **Client Summary** tab and **Progress & Analytics** tab (embedded chart placeholder + AI program Treeview). All data via Flask API. Run locally when you have a display.

---

## Local Setup and Execution

### Prerequisites

- Python 3.11+
- pip
- Display (only for running the Tkinter GUI)

### 1. Clone and enter the project

```bash
git clone https://github.com/amit93566/devops-assignment
cd flask_app
```

### 2. Virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# or: venv\Scripts\activate   # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

**Start the Flask backend:**

```bash
python app.py
```

Or with Gunicorn:

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

Backend runs at **http://localhost:5000**.

**Start the Tkinter frontend** (in another terminal, with venv activated):

```bash
python gui.py
```

The GUI loads programs and clients from the API. Select a client from the dropdown or enter name and Load; use Log Workout / Log Body Metrics to record data; view charts and BMI in the Progress & Analytics tab.

---

## Running Tests Manually

From the project root (with dependencies installed):

```bash
pytest tests/ -v
```

Tests target the Flask app (routes, status codes, JSON responses). Optional coverage:

```bash
pip install pytest-cov
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Docker

### Build the image

```bash
docker build -t aceest-fitness:latest .
```

### Run the Flask API in the container

```bash
docker run -p 5000:5000 aceest-fitness:latest
```

Then run `python gui.py` on the host and point it at `http://localhost:5000` (default).

### Run tests inside the container

```bash
docker run --rm aceest-fitness:latest pytest tests/ -v
```

---

## CI/CD Overview

### GitHub Actions (`.github/workflows/main.yml`)

Runs on every **push** and **pull_request** to `main`/`master`:

1. **Build & Lint** – Set up Python, install deps, run `python -m py_compile app.py`.
2. **Docker Image Build** – Build the Flask app image.
3. **Automated Testing** – Run the Pytest suite inside the container against the Flask application.

### Jenkins BUILD Phase

Configure a Jenkins job to pull this repo from GitHub and run a clean build (e.g. `docker build` and `docker run ... pytest tests/ -v`) as a secondary validation layer.

---

## Repository Layout

| Path | Description |
|------|-------------|
| `app.py` | Flask backend (API and service endpoints) |
| `gui.py` | Tkinter frontend (desktop client for the API) |
| `program_data.py` | Program specification data (used by backend and tests) |
| `requirements.txt` | Dependencies (Flask, Gunicorn, requests, pytest) |
| `tests/test_app.py` | Pytest suite for the Flask application |
| `Dockerfile` | Container image for the Flask backend |
| `.github/workflows/main.yml` | GitHub Actions CI/CD workflow |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | App info and API links (JSON) |
| GET | `/health` | Health check (JSON) |
| GET | `/api/programs` | List of program names (JSON) |
| GET | `/api/program/<name>` | Workout, diet, color, calorie_factor (JSON); 404 if not found |
| GET | `/api/clients` | List of all clients (JSON) |
| GET | `/api/clients/<name>` | One client by name (JSON); 404 if not found |
| POST | `/api/clients` | Create or replace client; JSON: name, program, age, weight, calories |
| POST | `/api/progress` | Save progress; JSON: client_name, week, adherence |

Program names: **Fat Loss (FL)**, **Muscle Gain (MG)**, **Beginner (BG)**. SQLite DB `aceest_fitness.db` is created by the Flask app (clients + progress tables). The GUI uses these endpoints only; no local DB.
