# Jenkins for Playlist Backend (Dockerized)

This folder contains a minimal Jenkins setup (Docker) + example `Jenkinsfile` to build, test, push, and deploy your **playlist-backend** images.

## Files
- `Dockerfile` – Extends Jenkins LTS, installs Docker CLI and common plugins.
- `docker-compose.yml` – Starts Jenkins with access to host Docker (via `/var/run/docker.sock`).
- `init.groovy.d/security.groovy` – Creates an initial admin user (change env vars!).
- `../Jenkinsfile` – Example pipeline (place at the repository root).

## Quick Start
```bash
cd jenkins-setup
docker compose up -d --build
# open http://<host>:8080
# login with admin / changeMeNow (change in compose env!)