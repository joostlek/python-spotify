"""Asynchronous Python client for Spotify."""
from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp.hdrs import METH_GET
from aioresponses import aioresponses

from . import load_fixture
from .const import HEADERS, SPOTIFY_URL

if TYPE_CHECKING:
    from spotifyaio import SpotifyClient
    from syrupy import SnapshotAssertion


async def test_get_current_user(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving current user."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me",
        status=200,
        body=load_fixture("current_user.json"),
    )
    response = await authenticated_client.get_current_user()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me",
        METH_GET,
        headers=HEADERS,
        params=None,
        data=None,
    )


async def test_get_user(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving user."""
    responses.get(
        f"{SPOTIFY_URL}/v1/users/smedjan",
        status=200,
        body=load_fixture("user.json"),
    )
    response = await authenticated_client.get_user("smedjan")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/users/smedjan",
        METH_GET,
        headers=HEADERS,
        params=None,
        data=None,
    )
