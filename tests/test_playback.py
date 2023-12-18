"""Asynchronous Python client for Spotify."""

from aiohttp.hdrs import METH_GET, METH_PUT
from aioresponses import aioresponses
import pytest

from spotifyaio.spotify import SpotifyClient
from syrupy import SnapshotAssertion

from . import load_fixture
from .const import HEADERS, SPOTIFY_URL


@pytest.mark.parametrize(
    "playback_id",
    [
        1,
        2,
        3,
    ],
)
async def test_get_playback_state(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    playback_id: int,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player",
        status=200,
        body=load_fixture(f"playback_{playback_id}.json"),
    )
    response = await authenticated_client.get_playback()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player",
        METH_GET,
        headers=HEADERS,
        params=None,
        data=None,
    )


async def test_get_no_playback_state(
    authenticated_client: SpotifyClient,
    responses: aioresponses,
) -> None:
    """Test retrieving no playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player",
        status=204,
    )
    response = await authenticated_client.get_playback()
    assert response is None
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player",
        METH_GET,
        headers=HEADERS,
        data=None,
        params=None,
    )


async def test_transfer_playback(
    authenticated_client: SpotifyClient,
    responses: aioresponses,
) -> None:
    """Test transferring playback."""
    responses.put(
        f"{SPOTIFY_URL}/v1/me/player",
        status=204,
    )
    await authenticated_client.transfer_playback("test")
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player",
        METH_PUT,
        headers=HEADERS,
        data={"device_ids": ["test"]},
        params=None,
    )


async def test_get_devices(
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
    responses: aioresponses,
) -> None:
    """Test retrieving devices."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player/devices",
        status=200,
        body=load_fixture("devices.json"),
    )
    devices = await authenticated_client.get_devices()
    assert devices == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/devices",
        headers=HEADERS,
        data=None,
        params=None,
    )


async def test_get_current_playing(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving current playing."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player/currently-playing",
        status=200,
        body=load_fixture("current_playing_track.json"),
    )
    response = await authenticated_client.get_current_playing()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/currently-playing",
        headers=HEADERS,
        data=None,
        params=None,
    )


async def test_get_no_current_playing_state(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving no current playing state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player/currently-playing",
        status=204,
    )
    response = await authenticated_client.get_current_playing()
    assert response is None
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/currently-playing",
        headers=HEADERS,
        params=None,
        data=None,
    )


async def test_resume_playback(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test resuming playback."""
    responses.put(
        f"{SPOTIFY_URL}/v1/me/player/play",
        status=204,
    )
    await authenticated_client.start_playback()
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/play",
        METH_PUT,
        headers=HEADERS,
        params={},
        data={"position_ms": 0},
    )
