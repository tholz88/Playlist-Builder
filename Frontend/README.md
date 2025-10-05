# Playlist Builder => Frontend

GET

/spotify/create-url?name={PlaylistName}

Rückgabe:

{
"url": "https://accounts.spotify.com/authorize?client_id=afb6bec096104319a37dd6d161f53bca&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Fspotify%2Fcallback&scope=playlist-modify-public+playlist-modify-private&state=XSeBgRYDiHuTA65Ob2ucQJOmlyIOOqZL"
}

## Todo
- Playwright Codegen in Projekt importieren -> https://chatgpt.com/c/68da6fa5-0ab4-832a-a603-44b05ee6ed31
- Functional test, develop-test