"""Spotify client for handling connections with Spotify."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Awaitable, Callable, Self

from aiohttp import ClientSession
from aiohttp.hdrs import METH_GET
from yarl import URL

from spotifyaio.exceptions import SpotifyConnectionError, SpotifyError
from spotifyaio.models import PlaybackState


@dataclass
class SpotifyClient:
    """Main class for handling connections with Spotify."""

    session: ClientSession | None = None
    request_timeout: int = 10
    api_host: str = "api.spotify.com"
    _token: str | None = None
    _close_session: bool = False
    refresh_token_function: Callable[[], Awaitable[str]] | None = None

    async def refresh_token(self) -> None:
        """Refresh token with provided function."""
        if self.refresh_token_function:
            self._token = await self.refresh_token_function()

    def authenticate(self, token: str) -> None:
        """Authenticate the user with a token."""
        self._token = token

    async def _request(
        self,
        uri: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Handle a request to Spotify."""
        version = metadata.version(__package__)
        url = URL.build(
            scheme="https",
            host=self.api_host,
            port=443,
        ).joinpath(uri)

        await self.refresh_token()

        headers = {
            "User-Agent": f"AioSpotify/{version}",
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {self._token}",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    METH_GET,
                    url,
                    headers=headers,
                    data=data,
                )
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to Spotify"
            raise SpotifyConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")

        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected response from Spotify"
            raise SpotifyError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return await response.text()

    async def get_playback(self) -> PlaybackState:
        """Get devices."""
        response = await self._request("v1/me/player")
        return PlaybackState.from_json(response)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The SpotifyClient object.
        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.
        """
        await self.close()
