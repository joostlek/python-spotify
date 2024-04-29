"""Asynchronous Python client for Spotify."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
from aioresponses import CallbackResult, aioresponses
import pytest

from spotifyaio import SpotifyClient, SpotifyConnectionError, SpotifyError

from . import load_fixture
from .const import SPOTIFY_URL


async def test_putting_in_own_session(
    responses: aioresponses,
) -> None:
    """Test putting in own session."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player",
        status=200,
        body=load_fixture("playback_1.json"),
    )
    async with aiohttp.ClientSession() as session:
        spotify = SpotifyClient(session=session)
        spotify.authenticate("test")
        await spotify.get_playback()
        assert spotify.session is not None
        assert not spotify.session.closed
        await spotify.close()
        assert not spotify.session.closed


async def test_creating_own_session(
    responses: aioresponses,
) -> None:
    """Test creating own session."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player",
        status=200,
        body=load_fixture("playback_1.json"),
    )
    spotify = SpotifyClient()
    spotify.authenticate("test")
    await spotify.get_playback()
    assert spotify.session is not None
    assert not spotify.session.closed
    await spotify.close()
    assert spotify.session.closed


async def test_refresh_token() -> None:
    """Test refreshing token."""

    async def _get_token() -> str:
        return "token"

    async with SpotifyClient() as spotify:
        assert spotify._token is None  # pylint: disable=protected-access
        await spotify.refresh_token()
        assert spotify._token is None  # pylint: disable=protected-access

        spotify.refresh_token_function = _get_token
        await spotify.refresh_token()

        assert spotify._token == "token"  # pylint: disable=protected-access


async def test_unexpected_server_response(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test handling unexpected response."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player",
        status=200,
        headers={"Content-Type": "plain/text"},
        body="Yes",
    )
    with pytest.raises(SpotifyError):
        assert await authenticated_client.get_playback()


async def test_timeout(
    responses: aioresponses,
) -> None:
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: str, **_kwargs: Any) -> CallbackResult:
        """Response handler for this test."""
        await asyncio.sleep(2)
        return CallbackResult(body="Goodmorning!")

    responses.get(
        f"{SPOTIFY_URL}/v1/me/player",
        callback=response_handler,
    )
    async with SpotifyClient(request_timeout=1) as spotify:
        with pytest.raises(SpotifyConnectionError):
            assert await spotify.get_playback()
