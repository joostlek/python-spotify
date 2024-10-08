"""Constants for tests."""

from importlib import metadata

SPOTIFY_URL = "https://api.spotify.com"

version = metadata.version("spotifyaio")

HEADERS = {
    "User-Agent": f"AioSpotify/{version}",
    "Accept": "application/json, text/plain, */*",
    "Authorization": "Bearer test",
}
