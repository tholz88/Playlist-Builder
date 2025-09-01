import time

# ---------- /playlist ----------
def test_get_playlist_initially_empty(client):
    r = client.get("/playlist")
    assert r.status_code == 200
    assert r.get_json() == {"playlist": []}
    assert r.headers.get("Access-Control-Allow-Origin") == "*"


# ---------- /search ----------
def test_search_spotify_success(client, fake_requests):
    def fake_token_post(url, data=None, headers=None, timeout=10):
        if "accounts.spotify.com/api/token" in url and data.get("grant_type") == "client_credentials":
            class _Resp:
                status_code = 200
                def json(self):
                    return {"access_token": "abc", "expires_in": 3600}
            return _Resp()
        class _Fail:
            status_code = 500
            def json(self): return {}
        return _Fail()

    def fake_search_get(url, headers=None, params=None, timeout=10):
        assert headers["Authorization"] == "Bearer abc"
        class _Resp:
            status_code = 200
            def json(self):
                return {
                    "tracks": {
                        "items": [{
                            "id": "track123",
                            "name": "Song A",
                            "artists": [{"name": "Artist A"}],
                            "album": {"name": "Album A"},
                            "duration_ms": 123000,
                            "preview_url": None,
                            "uri": "spotify:track:track123",
                            "external_urls": {"spotify": "https://open.spotify.com/track/track123"}
                        }]
                    }
                }
        return _Resp()

    fake_requests.post = fake_token_post
    fake_requests.get  = fake_search_get

    r = client.post("/search", json={"search": "Song A"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["results"][0]["id"] == "track123"
    assert data["results"][0]["title"] == "Song A"
    assert data["results"][0]["artist"] == "Artist A"


def test_search_spotify_requires_body(client):
    r = client.post("/search", data="{}", headers={"Content-Type": "application/json"})
    assert r.status_code == 400
    assert "error" in r.get_json()


# ---------- /add/<id> & /remove/<id> ----------
def test_add_and_remove_track(client, fake_requests):
    def fake_token_post(url, data=None, headers=None, timeout=10):
        if "accounts.spotify.com/api/token" in url and data.get("grant_type") == "client_credentials":
            class _Resp:
                status_code = 200
                def json(self):
                    return {"access_token": "abc", "expires_in": 3600}
            return _Resp()
        class _Fail:
            status_code = 500
            def json(self): return {}
        return _Fail()

    def fake_track_get(url, headers=None, params=None, timeout=10):
        assert "v1/tracks/track123" in url
        class _Resp:
            status_code = 200
            def json(self):
                return {
                    "id": "track123",
                    "name": "Song A",
                    "artists": [{"name": "Artist A"}]
                }
        return _Resp()

    fake_requests.post = fake_token_post
    fake_requests.get  = fake_track_get

    r = client.post("/add/track123")
    assert r.status_code == 201
    payload = r.get_json()
    assert payload["track"]["id"] == "track123"
    assert payload["track"]["source"] == "spotify"

    r2 = client.post("/remove/track123")
    assert r2.status_code == 200
    assert r2.get_json()["track"]["id"] == "track123"

    r3 = client.post("/remove/track123")
    assert r3.status_code == 404
    assert "error" in r3.get_json()


# ---------- /spotify/create-url ----------
def test_spotify_create_url(client):
    r = client.get("/spotify/create-url?name=My%20Cool%20Playlist")
    assert r.status_code == 200
    url = r.get_json()["url"]
    assert "accounts.spotify.com/authorize" in url
    assert "client_id=" in url
    assert "state=" in url
    assert "redirect_uri=" in url


# ---------- /spotify/callback ----------
def test_spotify_callback_creates_playlist_and_adds_tracks(client, fake_requests):
    import main as main_module

    main_module.playlist[:] = [
        {"id": "t1", "title": "A", "artist": "X", "source": "spotify"},
        {"id": "t2", "title": "B", "artist": "Y", "source": "spotify"},
    ]

    state_value = "STATE123"
    main_module._pending_states[state_value] = {"name": "PyTest List", "created_at": time.time()}

    def fake_post(url, json=None, data=None, headers=None, timeout=15):
        if "accounts.spotify.com/api/token" in url and data and data.get("grant_type") == "authorization_code":
            class _TokenOK:
                status_code = 200
                def json(self):
                    return {"access_token": "userAT"}
            return _TokenOK()

        if "api.spotify.com/v1/me/playlists" in url:
            class _CreateOK:
                status_code = 201
                def json(self):
                    return {"id": "pl123", "external_urls": {"spotify": "https://open.spotify.com/playlist/pl123"}}
            return _CreateOK()

        if "api.spotify.com/v1/playlists/pl123/tracks" in url:
            class _AddOK:
                status_code = 201
                def json(self): return {}
            return _AddOK()

        class _Fail:
            status_code = 500
            def json(self): return {}
        return _Fail()

    fake_requests.post = fake_post

    r = client.get("/spotify/callback?code=AUTHCODE&state=STATE123", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "open.spotify.com/playlist/pl123" in (r.headers.get("Location") or "")


# ---------- /spotify/callback Errors ----------
def test_spotify_callback_invalid_state(client):
    r = client.get("/spotify/callback?code=abc&state=unknown")
    assert r.status_code == 400
    assert r.get_json()["error"] in ("invalid_state_or_code",)


def test_spotify_callback_error_param(client):
    r = client.get("/spotify/callback?error=access_denied")
    assert r.status_code == 400
    assert r.get_json()["error"] == "access_denied"