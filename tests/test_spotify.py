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


async def test_get_album(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving album."""
    responses.get(
        f"{SPOTIFY_URL}/v1/albums/3IqzqH6ShrRtie9Yd2ODyG",
        status=200,
        body=load_fixture("get_album.json"),
    )
    response = await authenticated_client.get_album("3IqzqH6ShrRtie9Yd2ODyG")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/albums/3IqzqH6ShrRtie9Yd2ODyG",
        METH_GET,
        headers=HEADERS,
        params=None,
        data=None,
    )
