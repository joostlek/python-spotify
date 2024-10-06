"""Asynchronous Python client for Spotify."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp.hdrs import METH_GET
from aioresponses import aioresponses
import pytest

from . import load_fixture
from .const import HEADERS, SPOTIFY_URL

if TYPE_CHECKING:
    from spotifyaio import SpotifyClient
    from syrupy import SnapshotAssertion


async def test_get_playlist(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playlist."""
    responses.get(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        status=200,
        body=load_fixture("playlist.json"),
    )
    response = await authenticated_client.get_playlist("37i9dQZF1DXcBWIGoYBM5M")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        METH_GET,
        headers=HEADERS,
        params=None,
        data=None,
    )


@pytest.mark.parametrize(
    "playlist_id",
    [
        "37i9dQZF1DXcBWIGoYBM5M",
        "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
        "spotify:user:chilledcow:playlist:37i9dQZF1DXcBWIGoYBM5M",
    ],
)
async def test_get_playlist_variation(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    playlist_id: str,
) -> None:
    """Test retrieving playlist with different inputs."""
    responses.get(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        status=200,
        body=load_fixture("playlist.json"),
    )
    await authenticated_client.get_playlist(playlist_id)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        METH_GET,
        headers=HEADERS,
        params=None,
        data=None,
    )


async def test_get_current_users_playlists(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/playlists?limit=48",
        status=200,
        body=load_fixture("current_user_playlist.json"),
    )
    response = await authenticated_client.get_playlists_for_current_user()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/playlists",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        data=None,
    )


async def test_get_featured_playlists(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/browse/featured-playlists?limit=48",
        status=200,
        body=load_fixture("featured_playlists.json"),
    )
    response = await authenticated_client.get_featured_playlists()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/browse/featured-playlists",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        data=None,
    )


async def test_get_category_playlists(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/browse/categories/rock/playlists?limit=48",
        status=200,
        body=load_fixture("category_playlists.json"),
    )
    response = await authenticated_client.get_category_playlists("rock")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/browse/categories/rock/playlists",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        data=None,
    )
