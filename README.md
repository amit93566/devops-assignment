# ACEest Fitness & Gym

A Flask backend API plus Tkinter desktop frontend for fitness and gym management. Program data is served by the Flask API and consumed by the Tkinter GUI or any HTTP client. Includes CI/CD via GitHub Actions and Jenkins BUILD.

---

## Architecture

- **Backend (Flask)** – `app.py` exposes REST endpoints: **POST /api/login**; `/api/programs`, `/api/program/<name>`, `/api/clients` (GET/POST; name required, program optional), `/api/clients/<name>` (GET), plus progress, metrics, workouts. DB: `aceest_fitness.db` (users; clients with **membership_status**, **membership_end**; progress; workouts; exercises; metrics). Runs in Docker and in CI.
- **Frontend (Tkinter)** – `gui.py` (Aceestver-3.2.4): **Login** on root (admin/admin) → **Dashboard**: left panel **Select Client**, **Add / Save Client** (name + Active), **Generate AI Program** (random from templates), **Generate PDF Report**, **Check Membership**; right panel **Client Summary** (text + adherence chart) and **Workouts & Exercises** (Treeview + Add Workout). All data via Flask API. Run locally when you have a display.

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

Log in with **admin** / **admin**. Use **Select Client** to choose a client, **Add / Save Client** to create one, **Generate AI Program** and **Generate PDF Report** as needed; **Check Membership** shows status. The **Client Summary** tab shows profile and adherence chart; **Workouts & Exercises** lists workouts and lets you add new ones.

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

Then run `python gui.py` on the host; it uses **http://localhost:5000** by default.

### Run tests inside the container

```bash
docker run --rm aceest-fitness:latest pytest tests/ -v
```

---

## CI/CD Overview

### GitHub Actions (`.github/workflows/main.yml`)

Runs on every **push** and **pull_request** to the default branch:

1. **Build & Lint** – Set up Python, install dependencies, run `python -m py_compile` on the application to check syntax.
2. **Docker Image Assembly** – Build the Flask app Docker image.
3. **Automated Testing** – Run the Pytest suite inside the container against the Flask application.

### Jenkins BUILD Phase

Jenkins is used as a secondary validation layer: it pulls the repo from GitHub and runs a clean build (Docker build + run tests). See **Jenkins Setup** below.

---

## Jenkins Setup

1. **Install Jenkins** (if not already):
   - On Ubuntu/Debian: `sudo apt install openjdk-11-jdk` then add the Jenkins repo and install `jenkins`.
   - Or use the official Jenkins Docker image.

2. **Install required plugins** (Manage Jenkins → Plugins):
   - **Pipeline**
   - **Git** (and optionally **GitHub** for repo URL)
   - **Docker Pipeline** (optional, if you run Docker inside Jenkins)

3. **Ensure Docker is available** to the Jenkins user (if the pipeline runs `docker`):
   - Add the Jenkins user to the `docker` group: `sudo usermod -aG docker jenkins`
   - Restart Jenkins: `sudo systemctl restart jenkins`

4. **Create a Pipeline job**:
   - **New Item** → enter name (e.g. `aceest-fitness`) → **Pipeline** → **OK**.
   - In the job’s **Configure** screen:
     - **Pipeline** section:
       - **Definition**: Pipeline script from SCM.
       - **SCM**: Git.
       - **Repository URL**: your GitHub repo (e.g. `https://github.com/amit93566/devops-assignment.git`).
       - **Branch**: `*/main` or `*/master` (match your default branch).
       - **Script Path**: `Jenkinsfile` (root of repo).
       - For a private repo: add credentials under **Manage Jenkins → Credentials** and select them here.
     - **Build Triggers** (optional – for automatic builds):
       - **GitHub hook trigger for GITScm polling**: build runs on every push/PR (requires a webhook in GitHub repo **Settings → Webhooks** pointing to `http://<JENKINS_URL>/github-webhook/`).
       - Or **Poll SCM**: e.g. schedule `H/5 * * * *` so Jenkins checks GitHub every 5 minutes and builds if there are new commits.
   - **Save**.

5. **Run the build**:
   - **Manual**: Click **Build Now**. The pipeline checks out the repo and runs the stages in `Jenkinsfile` (checkout, Docker build, then `docker run ... pytest tests/ -v`).
   - **Automatic**: If you enabled a build trigger above, each push to GitHub (or each poll that finds changes) will start a build automatically.

6. **Troubleshooting**:
   - If Docker commands fail with “permission denied”, ensure the Jenkins user is in the `docker` group and Jenkins was restarted.
   - If the repo is private, add credentials in Jenkins (Username/Password or SSH key) and select them in the job’s Git configuration.

---

## Repository Layout

| Path | Description |
|------|-------------|
| `app.py` | Flask backend (API and service endpoints) |
| `gui.py` | Tkinter frontend (desktop client for the API) |
| `program_data.py` | Program specification data (used by backend and tests) |
| `requirements.txt` | Dependencies (Flask, Gunicorn, requests, matplotlib, fpdf2, pytest) |
| `tests/test_app.py` | Pytest suite for the Flask application |
| `Dockerfile` | Container image for the Flask backend |
| `Jenkinsfile` | Jenkins Pipeline definition (checkout, build, test) |
| `.github/workflows/main.yml` | GitHub Actions CI/CD workflow |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | App info and API links (JSON) |
| GET | `/health` | Health check (JSON) |
| POST | `/api/login` | Login; JSON: username, password → username, role; 401 if invalid |
| GET | `/api/programs` | List of program names (JSON) |
| GET | `/api/program/<name>` | Workout, diet, color, calorie_factor, desc (JSON); 404 if not found |
| GET | `/api/clients` | List of all clients (JSON) |
| GET | `/api/clients/<name>` | One client by name (JSON); 404 if not found |
| POST | `/api/clients` | Create or replace client; JSON: name (required), program (optional), age, height, weight, calories, membership_status, membership_end |
| POST | `/api/progress` | Save progress; JSON: client_name, week, adherence |
| GET | `/api/progress/<client_name>` | List progress entries (week, adherence) for client |
| POST | `/api/metrics` | Save body metrics; JSON: client_name, date, weight, waist, bodyfat |
| GET | `/api/metrics/<client_name>` | List metrics for client |
| POST | `/api/workouts` | Save workout; JSON: client_name, date, workout_type, duration_min, notes |
| GET | `/api/workouts/<client_name>` | List workouts for client |

Program names are returned by `/api/programs`. SQLite DB `aceest_fitness.db` is created by the Flask app. The GUI uses these endpoints only; no local DB.
