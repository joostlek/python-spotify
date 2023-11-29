"""Asynchronous Python client for Spotify."""


class SpotifyError(Exception):
    """Generic exception."""


class SpotifyConnectionError(SpotifyError):
    """Spotify connection exception."""


class SpotifyAuthenticationFailedError(SpotifyError):
    """Spotify authentication failed exception."""
