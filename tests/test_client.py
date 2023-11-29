"""Asynchronous Python client for Spotify."""
from __future__ import annotations

import asyncio

import aiohttp
from aiohttp.hdrs import METH_GET
from aiohttp.web_request import BaseRequest
from aresponses import Response, ResponsesMockServer
import pytest

from spotifyaio import SpotifyClient, SpotifyConnectionError, SpotifyError

from . import load_fixture
from .const import SPOTIFY_URL


async def test_own_session(
    aresponses: ResponsesMockServer,
) -> None:
    """Test creating own session."""
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
        await spotify.get_playback()
        assert spotify.session is not None


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
    aresponses: ResponsesMockServer,
) -> None:
    """Test handling unexpected response."""
    aresponses.add(
        SPOTIFY_URL,
        "/v1/me/player",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "plain/text"},
            text="Yes",
        ),
    )
    async with SpotifyClient() as spotify:
        spotify.authenticate("test")
        with pytest.raises(SpotifyError):
            assert await spotify.get_playback()


async def test_timeout(aresponses: ResponsesMockServer) -> None:
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: BaseRequest) -> Response:
        """Response handler for this test."""
        await asyncio.sleep(2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add(
        SPOTIFY_URL,
        "/v1/me/player",
        METH_GET,
        response_handler,
    )
    async with aiohttp.ClientSession() as session:
        spotify = SpotifyClient(session=session, request_timeout=1)
        spotify.authenticate("test")
        with pytest.raises(SpotifyConnectionError):
            assert await spotify.get_playback()
        await spotify.close()
