## 1. Overview

ACEest Fitness & Gym is a Flask backend API with a Tkinter desktop frontend for fitness and gym management. The application supports user login, client management, membership tracking, AI-style program generation, PDF reports, and workout logging.

The project implements a complete DevOps pipeline including:
- Version Control (Git/GitHub)
- Unit Testing (Pytest)
- Code Quality (SonarQube)
- Containerization (Docker)
- CI/CD (GitHub Actions + Jenkins)
- Container Registry (Docker Hub)
- Orchestration (Minikube + AWS EKS)



## 2. Architecture

**Backend (Flask):** `app.py` provides REST endpoints for login, programs, clients, progress, metrics, and workouts. Data is stored in SQLite (`aceest_fitness.db`).

**Frontend (Tkinter):** `gui.py` is a desktop client that logs in (admin/admin), then shows a dashboard with client selection, Add/Save Client, Generate AI Program, Generate PDF Report, Check Membership, Client Summary with adherence chart, and Workouts & Exercises tab.



## 3. Version History

| Version | Main Features |
|---------|--------------|
| 1.0 | Basic Tkinter UI, program selection (Fat Loss, Muscle Gain, Beginner) |
| 1.1 | Simplified UI, program selection and display |
| 1.1.2 | Client list, CSV export, matplotlib progress chart |
| 2.2.1 | Client Management, Save/Load Client, Save Progress, View Progress Chart |
| 2.2.4 | Status bar, Select Client combobox, Notebook tabs, Log Workout, Log Body Metrics |
| 3.0.1 | Same feature set as 2.2.4 (version label only) |
| 3.1.2 | Login, Dashboard, Membership Expiry, Generate AI Program, Export PDF Report |
| 3.2.4 | Login on root, membership_status, Add/Save Client, Generate AI Program, Generate PDF Report, Check Membership, Workouts & Exercises tab |

---

## 4. Local Setup and Execution

### Prerequisites
- Python 3.11+
- pip
- Display (for running the Tkinter GUI)

### Steps

**1. Clone the repository:**
```bash
git clone https://github.com/amit93566/devops-assignment.git
cd devops-assignment
```

**2. Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# or: venv\Scripts\activate     # Windows
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Start the Flask backend:**
```bash
python app.py
# Or with Gunicorn:
gunicorn --bind 0.0.0.0:5000 app:app
```
Backend runs at `http://localhost:5000`

**5. Start the Tkinter frontend (in another terminal):**
```bash
python gui.py
```
Login with **admin / admin**



## 5. Running Tests Manually

```bash
pytest tests/ -v
```

Tests cover Flask routes, status codes, and JSON responses. 26 tests total, all passing.

Optional coverage report:
```bash
pip install pytest-cov
pytest tests/ -v --cov=app --cov-report=term-missing
```


## 6. Docker

### Build the image
```bash
docker build -t aceest-fitness:latest .
```

### Run the Flask API
```bash
docker run -p 5000:5000 aceest-fitness:latest
```

### Run tests inside container
```bash
docker run --rm aceest-fitness:latest pytest tests/ -v
```


## 7. Docker Hub

Images are versioned and pushed to Docker Hub:

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable build |
| `v1.0` | Version 1.0 — stable production |
| `v2.0` | Version 2.0 — new release |

```bash
docker pull 2024tm93566bits/aceest_fitness_image:latest
docker pull 2024tm93566bits/aceest_fitness_image:v1.0
docker pull 2024tm93566bits/aceest_fitness_image:v2.0
```



## 8. GitHub Actions CI/CD

Defined in `.github/workflows/main.yml`. Runs on every push and pull request to the main branch.

**Stages:**
1. **Build & Lint** — Set up Python, install dependencies, run `python -m py_compile` to check syntax
2. **Docker Image Assembly** — Build the Flask application Docker image
3. **Automated Testing** — Run the Pytest suite inside the container



## 9. Jenkins Pipeline

Jenkins is used as a secondary validation layer. The pipeline is defined in `Jenkinsfile`.

**Pipeline Stages:**
1. **Checkout** — Pull latest code from GitHub
2. **Install Dependencies** — `pip install -r requirements.txt --break-system-packages`
3. **Run Tests** — `python3 -m pytest --tb=short` (26 tests)
4. **SonarQube Analysis** — Static code analysis with quality gate enforcement
5. **Build Docker Image** — `docker build -t aceest-fitness:latest .`

**Jenkins Setup:**
- Job type: Pipeline
- Trigger: Poll SCM (`H/5 * * * *`) — every 5 minutes
- Pipeline definition: Pipeline script from SCM (Git)
- Repository URL: `https://github.com/amit93566/devops-assignment.git`
- Script Path: `Jenkinsfile`



## 10. SonarQube Code Quality

SonarQube Community Edition (v10.4.1) is integrated into the Jenkins pipeline for static code analysis.

**Analysis Results:**
- **Quality Gate Status:** Passed ✅
- **Security:** 0 Open Issues (A)
- **Reliability:** 1 Open Issue (C)
- **Maintainability:** 11 Open Issues (A)
- **Lines of Code:** 1.1k
- **Duplications:** 0.0%

**Run analysis manually:**
```bash
/opt/sonar-scanner/bin/sonar-scanner \
  -Dsonar.projectKey=aceest-fitness \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token=YOUR_TOKEN
```



## 11. Kubernetes Deployment Strategies

The application is deployed on both **Minikube (local)** and **AWS EKS (cloud)** using 5 deployment strategies. Each strategy uses two versions:
- **v1.0** — Stable/Production version
- **v2.0** — New/Test version

### AWS EKS Cluster Details
- **Cluster Name:** aceest-fitness-cluster
- **Region:** eu-north-1
- **Node Type:** t3.small
- **Nodes:** 2 (min: 1, max: 3)

### Deployment Strategies

| Strategy | YAML File | Description |
|----------|-----------|-------------|
| Blue-Green | `k8s/blue-green-deployment.yaml` | v1.0 (blue) serves traffic; switch to v2.0 (green) for zero-downtime update |
| Canary | `k8s/canary-deployment.yaml` | 75% traffic to v1.0 (stable), 25% to v2.0 (canary) |
| Rolling Update | `k8s/rolling-update-deployment.yaml` | Gradually replace v1.0 pods with v2.0 |
| A/B Testing | `k8s/ab-testing-deployment.yaml` | v1.0 (version-a) vs v2.0 (version-b) for comparison |
| Shadow | `k8s/shadow-deployment.yaml` | v1.0 serves real traffic; v2.0 mirrors silently |

### Deploy all strategies
```bash
kubectl apply -f k8s/blue-green-deployment.yaml
kubectl apply -f k8s/canary-deployment.yaml
kubectl apply -f k8s/rolling-update-deployment.yaml
kubectl apply -f k8s/ab-testing-deployment.yaml
kubectl apply -f k8s/shadow-deployment.yaml
```

### Rollback Commands

**Blue-Green — switch back to stable (blue/v1.0):**
```bash
kubectl patch service aceest-service -p '{"spec":{"selector":{"version":"blue"}}}'
```

**Canary — rollback canary to stable:**
```bash
kubectl scale deployment aceest-canary --replicas=0
kubectl scale deployment aceest-stable --replicas=3
```

**Rolling Update — rollback to previous version:**
```bash
kubectl rollout undo deployment/aceest-rolling
```

**A/B Testing — rollback version-b:**
```bash
kubectl scale deployment aceest-version-b --replicas=0
```

**Shadow — remove shadow deployment:**
```bash
kubectl scale deployment aceest-shadow --replicas=0
```

### AWS EKS Service Endpoints

| Strategy | External URL |
|----------|-------------|
| Blue-Green | `http://ab05a17cde82d4b219fb92895efc323e-582047219.eu-north-1.elb.amazonaws.com` |
| Canary | `http://af8266b7976b34805ad134cb90bb1c6f-604946243.eu-north-1.elb.amazonaws.com` |
| Rolling Update | `http://ac1d25ad2c735418cac438a6086d6485-909567311.eu-north-1.elb.amazonaws.com` |
| A/B Testing | `http://a6d3b951321154b3a9edda5cc4bc1dde-1914805219.eu-north-1.elb.amazonaws.com` |
| Shadow | `http://ad97a92b9f1234d528588cd3c4a4e241-156886867.eu-north-1.elb.amazonaws.com` |


## 12. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | App info and API links |
| GET | `/health` | Health check |
| POST | `/api/login` | Login with username and password |
| GET | `/api/programs` | List all program names |
| GET | `/api/program/<name>` | Get program details by name |
| GET | `/api/clients` | List all clients |
| GET | `/api/clients/<name>` | Get client by name |
| POST | `/api/clients` | Create or update client |
| POST | `/api/progress` | Save progress entry |
| GET | `/api/progress/<client_name>` | Get progress for client |
| POST | `/api/metrics` | Save body metrics |
| GET | `/api/metrics/<client_name>` | Get metrics for client |
| POST | `/api/workouts` | Save workout |
| GET | `/api/workouts/<client_name>` | Get workouts for client |

---

## 13. Repository Layout

| Path | Description |
|------|-------------|
| `app.py` | Flask backend API |
| `gui.py` | Tkinter frontend |
| `program_data.py` | Program specification data |
| `requirements.txt` | Python dependencies |
| `tests/test_app.py` | Pytest suite (26 tests) |
| `Dockerfile` | Container image definition |
| `Jenkinsfile` | Jenkins pipeline with SonarQube |
| `.github/workflows/main.yml` | GitHub Actions CI/CD workflow |
| `sonar-project.properties` | SonarQube configuration |
| `k8s/blue-green-deployment.yaml` | Blue-Green deployment strategy |
| `k8s/canary-deployment.yaml` | Canary deployment strategy |
| `k8s/rolling-update-deployment.yaml` | Rolling Update strategy |
| `k8s/ab-testing-deployment.yaml` | A/B Testing strategy |
| `k8s/shadow-deployment.yaml` | Shadow deployment strategy |



**Developed by:** Amit Kumar Rout (2024TM93566)  
