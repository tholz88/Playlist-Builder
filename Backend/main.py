import os
import time
import base64
import secrets
import urllib.parse
import requests
from flask import Flask, request, jsonify, redirect
from dotenv import load_dotenv

# =====================================================
#   Configuration & Environment
# =====================================================
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIFY_MARKET = os.getenv("SPOTIFY_MARKET", "CH")

# Spotify OAuth scopes: allows creating and modifying playlists
OAUTH_SCOPES = "playlist-modify-public playlist-modify-private"

app = Flask(__name__)

# =====================================================
#   Token Cache (Client Credentials)
# =====================================================
_spotify_token = None
_spotify_token_exp = 0

def get_spotify_token():
    """Fetch and cache an access token via Client Credentials."""
    global _spotify_token, _spotify_token_exp
    now = time.time()
    if _spotify_token and now < _spotify_token_exp - 60:
        return _spotify_token

    auth_b64 = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()

    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        headers={"Authorization": f"Basic {auth_b64}"},
        timeout=10,
    )
    if resp.status_code != 200:
        return None

    data = resp.json()
    _spotify_token = data["access_token"]
    _spotify_token_exp = now + int(data.get("expires_in", 3600))
    return _spotify_token

# =====================================================
#   Local Playlist Storage (in-memory)
# =====================================================
playlist = []
manual_id_counter = 1

# =====================================================
#   State Cache for OAuth
# =====================================================
_pending_states = {}

# =====================================================
#   Middleware: CORS headers
# =====================================================
@app.after_request
def add_cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp

# =====================================================
#   Playlist Endpoints
# =====================================================
@app.route("/playlist", methods=["GET"])
def get_playlist():
    """Return the current playlist (local in-memory)."""
    return jsonify({"playlist": playlist})

@app.route("/search", methods=["POST"])
def search_spotify():
    """Search for a track on Spotify by keyword."""
    body = request.get_json(silent=True) or {}
    query = (body.get("search") or "").strip()
    if not query:
        return jsonify({"error": "Please send JSON with a 'search' field."}), 400

    token = get_spotify_token()
    if not token:
        return jsonify({"error": "Spotify authentication failed."}), 502

    params = {"q": query, "type": "track", "limit": 1, "market": SPOTIFY_MARKET}
    r = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=10,
    )

    if r.status_code != 200:
        return jsonify({"error": "Spotify search failed", "status": r.status_code}), 502

    items = (r.json().get("tracks", {}).get("items", [])) or []
    results = []
    for t in items:
        results.append({
            "id": t.get("id"),
            "title": t.get("name"),
            "artist": ", ".join(a.get("name") for a in t.get("artists", [])),
            "album": (t.get("album") or {}).get("name"),
            "duration_ms": t.get("duration_ms"),
            "preview_url": t.get("preview_url"),
            "spotify_uri": t.get("uri"),
            "external_url": (t.get("external_urls") or {}).get("spotify"),
        })
    return jsonify({"results": results})

@app.route("/add/<track_id>", methods=["POST"])
def add_by_id(track_id):
    """Add a track to the local playlist by its Spotify ID."""
    token = get_spotify_token()
    if not token:
        return jsonify({"error": "Spotify authentication failed."}), 502

    r = requests.get(
        f"https://api.spotify.com/v1/tracks/{track_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"market": SPOTIFY_MARKET},
        timeout=10,
    )
    if r.status_code != 200:
        return jsonify({"error": "Spotify track lookup failed", "status": r.status_code}), 502

    t = r.json()
    entry = {
        "id": t.get("id"),
        "title": t.get("name"),
        "artist": ", ".join(a.get("name") for a in t.get("artists", [])),
        "source": "spotify",
    }
    playlist.append(entry)
    return jsonify({"message": "Added", "track": entry}), 201

@app.route("/remove/<any_id>", methods=["POST"])
def remove_by_id(any_id):
    """Remove a track from the local playlist by ID."""
    for i, it in enumerate(playlist):
        if it.get("id") == any_id:
            removed = playlist.pop(i)
            return jsonify({"message": "Removed", "track": removed})
    return jsonify({"error": f"No entry with ID '{any_id}' found in playlist."}), 404

# =====================================================
#   Spotify Helper Functions
# =====================================================
def build_spotify_uris_from_playlist():
    """Return all Spotify URIs from the local playlist."""
    return [f"spotify:track:{it['id']}" for it in playlist if it.get("source") == "spotify"]

def exchange_code_for_token(code):
    """Exchange authorization code for access token."""
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET,
        },
        timeout=15,
    )
    return resp.json() if resp.status_code == 200 else None

# =====================================================
#   Spotify OAuth Endpoints (Authorization Code Flow)
# =====================================================
@app.route("/spotify/create-url", methods=["GET"])
def spotify_create_url():
    """Generate a Spotify authorization URL with state handling."""
    desired_name = request.args.get("name", "My Playlist").strip()
    state = secrets.token_urlsafe(24)
    _pending_states[state] = {"name": desired_name, "created_at": time.time()}

    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": OAUTH_SCOPES,
        "state": state,
    }
    authorize_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return jsonify({"url": authorize_url})

@app.route("/spotify/callback", methods=["GET"])
def spotify_callback():
    """Spotify redirect handler: create a playlist and add tracks."""
    error = request.args.get("error")
    if error:
        return jsonify({"error": error}), 400

    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state or state not in _pending_states:
        return jsonify({"error": "invalid_state_or_code"}), 400

    tok = exchange_code_for_token(code)
    if not tok:
        return jsonify({"error": "token_exchange_failed"}), 502

    access_token = tok["access_token"]
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    desired = _pending_states.pop(state, {"name": "My Playlist"})
    playlist_name = desired.get("name", "My Playlist")

    # Create the playlist on the user's account
    create_resp = requests.post(
        "https://api.spotify.com/v1/me/playlists",
        headers=headers,
        json={"name": playlist_name, "public": True, "description": "Built with Playlist Builder"},
        timeout=15,
    )
    if create_resp.status_code not in (200, 201):
        return jsonify({"error": "create_playlist_failed", "status": create_resp.status_code}), 502

    created = create_resp.json()
    playlist_id = created["id"]
    playlist_url = created.get("external_urls", {}).get("spotify")

    # Add tracks to the new playlist
    uris = build_spotify_uris_from_playlist()
    if uris:
        requests.post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            headers=headers,
            json={"uris": uris},
            timeout=15,
        )

    return redirect(playlist_url) if playlist_url else jsonify({"playlist_id": playlist_id})

# =====================================================
#   Entry Point
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)