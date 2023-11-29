"""Asynchronous Python client for Spotify."""

import aiohttp
from aiohttp.hdrs import METH_GET
from aresponses import ResponsesMockServer

from spotifyaio.spotify import SpotifyClient
from syrupy import SnapshotAssertion

from . import load_fixture
from .const import SPOTIFY_URL


async def test_get_devices(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving devices."""
    aresponses.add(
        SPOTIFY_URL,
        "/v1/me/player",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("playback.json"),
        ),
    )
    async with aiohttp.ClientSession() as session:
        spotify = SpotifyClient(session=session)
        spotify.authenticate("test")
        response = await spotify.get_playback()
        assert response == snapshot
        await spotify.close()
