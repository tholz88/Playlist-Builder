# Playlist-Builder
Backend for Playlist Builder
# Playlist Builder – Backend

Small Flask API to build a playlist from Spotify searches, then create a real Spotify playlist via OAuth.

## Features
- `/search` → find a Spotify track (client-credentials flow)
- `/add/<track_id>` → add track to in-memory list
- `/playlist` → view in-memory playlist
- OAuth flow:
  - `GET /spotify/create-url?name=My%20Playlist` to get consent URL
  - Spotify redirects to `/spotify/callback` which creates a playlist on your account and adds the in-memory tracks

---

## Quick Start (without Docker)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# copy and edit env
cp .env.example .env

# run
python main.py
# → http://127.0.0.1:5000
