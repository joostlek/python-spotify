"""Asynchronous Python client for Spotify."""


class SpotifyError(Exception):
    """Generic exception."""


class SpotifyConnectionError(SpotifyError):
    """Spotify connection exception."""


class SpotifyAuthenticationFailedError(SpotifyError):
    """Spotify authentication failed exception."""


class SpotifyNotFoundError(SpotifyError):
    """Spotify not found exception."""


class SpotifyRateLimitError(SpotifyError):
    """Spotify rate limit exception."""


class SpotifyForbiddenError(SpotifyError):
    """Spotify forbidden (403) exception."""
