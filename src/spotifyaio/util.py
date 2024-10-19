"""Utility functions for the SpotifyAIO package."""


def get_identifier(identifier: str) -> str:
    """Get the identifier from a Spotify URI."""
    return identifier.split(":")[-1]
