"""Asynchronous Python client for Spotify."""

from aiohttp.hdrs import METH_GET, METH_PUT
from aresponses import ResponsesMockServer
import pytest

from spotifyaio.spotify import SpotifyClient
from syrupy import SnapshotAssertion

from . import load_fixture
from .const import SPOTIFY_URL


@pytest.mark.parametrize(
    "playback_id",
    [
        1,
        2,
        3,
    ],
)
async def test_get_playback_state(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    playback_id: int,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving devices."""
    aresponses.add(
        SPOTIFY_URL,
        "/v1/me/player",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture(f"playback_{playback_id}.json"),
        ),
    )
    response = await authenticated_client.get_playback()
    assert response == snapshot


async def test_get_no_playback_state(
    aresponses: ResponsesMockServer,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving devices."""
    aresponses.add(
        SPOTIFY_URL,
        "/v1/me/player",
        METH_GET,
        aresponses.Response(
            status=204,
            headers={"Content-Type": "application/json"},
        ),
    )
    response = await authenticated_client.get_playback()
    assert response is None


async def test_transfer_playback(
    aresponses: ResponsesMockServer,
    authenticated_client: SpotifyClient,
) -> None:
    """Test transferring playback."""
    aresponses.add(
        SPOTIFY_URL,
        "/v1/me/player",
        METH_PUT,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )
    await authenticated_client.transfer_playback("test")


async def test_get_devices(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test transferring playback."""
    aresponses.add(
        SPOTIFY_URL,
        "/v1/me/player/devices",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("devices.json"),
        ),
    )
    devices = await authenticated_client.get_devices()
    assert devices == snapshot
