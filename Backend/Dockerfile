# -------- Base --------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# -------- Prod Stage --------
FROM base AS prod

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://127.0.0.1:5000/playlist || exit 1

CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:5000", "main:app"]

# -------- Test Stage --------
FROM base AS test

RUN pip install --no-cache-dir pytest pytest-cov

ENV SPOTIFY_CLIENT_ID=dummy \
    SPOTIFY_CLIENT_SECRET=dummy \
    SPOTIFY_REDIRECT_URI=http://localhost:5000/spotify/callback \
    SPOTIFY_MARKET=CH

CMD ["pytest", "-q", "--maxfail=1", "--disable-warnings", "--cov=main", "--cov-report=term-missing"]