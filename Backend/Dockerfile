# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Prevents python from writing .pyc and enables unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (curl only for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements separately for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . /app

# Expose Flask/Gunicorn port
EXPOSE 5000

# Simple healthcheck hitting /playlist
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://127.0.0.1:5000/playlist || exit 1

# Run via gunicorn in production; module:function is main:app
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:5000", "main:app"]

