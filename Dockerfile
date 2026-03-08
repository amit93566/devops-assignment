# ACEest Fitness & Gym - Flask backend
# Container runs the API; tests run via pytest in CI.

FROM python:3.11-slim

RUN apt-get update --no-install-recommends -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py program_data.py .
COPY tests/ tests/

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "app:app"]
