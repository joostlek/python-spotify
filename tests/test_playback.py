"""Asynchronous Python client for Spotify."""

import aiohttp
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
    async with aiohttp.ClientSession() as session:
        spotify = SpotifyClient(session=session)
        spotify.authenticate("test")
        response = await spotify.get_playback()
        assert response == snapshot
        await spotify.close()


async def test_get_no_playback_state(
    aresponses: ResponsesMockServer,
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
    async with aiohttp.ClientSession() as session:
        spotify = SpotifyClient(session=session)
        spotify.authenticate("test")
        response = await spotify.get_playback()
        assert response is None
        await spotify.close()


async def test_transfer_playback(
    aresponses: ResponsesMockServer,
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
    async with aiohttp.ClientSession() as session:
        spotify = SpotifyClient(session=session)
        spotify.authenticate("test")
        await spotify.transfer_playback("test")
        await spotify.close()


async def test_get_devices(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
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
    async with aiohttp.ClientSession() as session:
        spotify = SpotifyClient(session=session)
        spotify.authenticate("test")
        devices = await spotify.get_devices()
        assert devices == snapshot
        await spotify.close()
