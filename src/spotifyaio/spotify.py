"""Spotify client for handling connections with Spotify."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Awaitable, Callable, Self

from aiohttp import ClientSession
from aiohttp.hdrs import METH_GET, METH_POST, METH_PUT
from yarl import URL

from spotifyaio.exceptions import SpotifyConnectionError, SpotifyError
from spotifyaio.models import CurrentPlaying, Device, Devices, PlaybackState, RepeatMode


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
        method: str,
        uri: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
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
                    method,
                    url,
                    headers=headers,
                    data=data,
                    params=params,
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

    async def _get(self, uri: str) -> str:
        """Handle a GET request to Spotify."""
        return await self._request(METH_GET, uri)

    async def _post(
        self,
        uri: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Handle a POST request to Spotify."""
        return await self._request(METH_POST, uri, data=data, params=params)

    async def _put(
        self,
        uri: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Handle a PUT request to Spotify."""
        return await self._request(METH_PUT, uri, data=data, params=params)

    async def get_playback(self) -> PlaybackState | None:
        """Get playback state."""
        response = await self._get("v1/me/player")
        if response == "":
            return None
        return PlaybackState.from_json(response)

    async def get_current_playing(self) -> CurrentPlaying | None:
        """Get playback state."""
        response = await self._get("v1/me/player/currently-playing")
        if response == "":
            return None
        return CurrentPlaying.from_json(response)

    async def transfer_playback(self, device_id: str) -> None:
        """Transfer playback."""
        await self._put("v1/me/player", {"device_ids": [device_id]})

    async def get_devices(self) -> list[Device]:
        """Get devices."""
        response = await self._get("v1/me/player/devices")
        return Devices.from_json(response).devices

    async def start_playback(
        self,
        *,
        device_id: str | None = None,
        context_uri: str | None = None,
        uris: list[str] | None = None,
        position_offset: int | None = None,
        uri_offset: str | None = None,
        position: int | None = 0,
    ) -> None:
        """Start playback."""
        payload: dict[str, Any] = {
            "position_ms": position,
        }
        if context_uri:
            payload["context_uri"] = context_uri
        if uris:
            payload["uris"] = uris
        if position_offset:
            payload["offset"] = {"position": position_offset}
        if uri_offset:
            payload["offset"] = {"uri": uri_offset}
        params = {}
        if device_id:
            params["device_id"] = device_id
        await self._put("v1/me/player/play", payload, params=params)

    async def pause_playback(self, device_id: str | None = None) -> None:
        """Pause playback."""
        params = {}
        if device_id:
            params["device_id"] = device_id
        await self._put("v1/me/player/pause", params=params)

    async def next_track(self, device_id: str | None = None) -> None:
        """Next track."""
        params: dict[str, str] = {}
        if device_id:
            params["device_id"] = device_id
        await self._post("v1/me/player/next", params=params)

    async def previous_track(self, device_id: str | None = None) -> None:
        """Previous track."""
        params: dict[str, str] = {}
        if device_id:
            params["device_id"] = device_id
        await self._post("v1/me/player/previous", params=params)

    async def seek_track(self, position: int, device_id: str | None = None) -> None:
        """Seek track."""
        params: dict[str, Any] = {"position_ms": position}
        if device_id:
            params["device_id"] = device_id
        await self._put("v1/me/player/seek", params=params)

    async def set_repeat(self, state: RepeatMode, device_id: str | None = None) -> None:
        """Set repeat."""
        params: dict[str, str] = {"state": state}
        if device_id:
            params["device_id"] = device_id
        await self._put("v1/me/player/repeat", params=params)

    async def set_volume(self, volume: int, device_id: str | None = None) -> None:
        """Set volume."""
        params: dict[str, Any] = {"volume_percent": volume}
        if device_id:
            params["device_id"] = device_id
        await self._put("v1/me/player/volume", params=params)

    async def set_shuffle(self, *, state: bool, device_id: str | None = None) -> None:
        """Set shuffle."""
        params: dict[str, Any] = {"state": str(state).lower()}
        if device_id:
            params["device_id"] = device_id
        await self._put("v1/me/player/shuffle", params=params)

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
