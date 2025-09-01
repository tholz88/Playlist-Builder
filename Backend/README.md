# Playlist Builder – Backend

A small Flask API to search Spotify tracks, build a local playlist, and then create a real Spotify playlist via OAuth.

## Endpoints

* `POST /search` – search Spotify
* `POST /add/<track_id>` – add a track to the in-memory playlist
* `POST /remove/<id>` – remove a track from the in-memory playlist
* `GET /playlist` – return the current in-memory playlist
* OAuth:

  * `GET /spotify/create-url?name=My%20Playlist` → generate Spotify consent URL
  * Spotify redirects to `/spotify/callback` → creates a playlist in your account and adds the tracks

---

## 1) Docker Deploy (Production)

### Requirements

* `.env` with:

  ```env
  SPOTIFY_CLIENT_ID=...
  SPOTIFY_CLIENT_SECRET=...
  SPOTIFY_REDIRECT_URI=http://localhost:5050/spotify/callback
  SPOTIFY_MARKET=CH
  ```
* `Dockerfile` (with `prod` stage) and `docker-compose.yml` as configured.

### Start

```bash
docker compose up -d --build backend
```

### Healthcheck

* Container: `playlist-backend`
* Internally checks: `http://127.0.0.1:5000/playlist`

### Ports

* Local access: `http://localhost:5050`

### Example calls

```bash
# Get playlist
curl -s http://localhost:5050/playlist | jq

# Search for a song
curl -s -X POST http://localhost:5050/search \
  -H 'Content-Type: application/json' \
  -d '{"search":"nirvana smells like teen spirit"}' | jq

# Add a track (replace with real ID from search)
curl -s -X POST http://localhost:5050/add/<track_id> | jq

# Generate OAuth URL and open in browser
curl -s "http://localhost:5050/spotify/create-url?name=My%20Playlist" | jq -r .url
```

---

## 2) Testing

### Tests via Docker

The `Dockerfile` has two stages:

* `prod` – production runtime with Gunicorn
* `test` – lightweight test image with pytest


**Run tests:**

```bash
docker compose build tests
docker compose run --rm tests
```

> The container exits immediately with the pytest exit code (0 = all tests passed).

---

## 3) Quick Start Matrix

| Goal               | Command                                                       |
| ------------------ | ------------------------------------------------------------- |
| Start production   | `docker compose up -d --build backend`                        |
| View logs          | `docker compose logs -f backend`                              |
| Run tests (Docker) | `docker compose build tests && docker compose run --rm tests` |
| Run tests (local)  | `pytest -q`                                                   |

---

## 4) Notes

* The in-memory playlist is **not persisted** (reset on restart).
* `SPOTIFY_REDIRECT_URI` must match the one registered in your Spotify Developer dashboard.
* Gunicorn runs on `0.0.0.0:5000`, Compose maps it to `5050:5000`.