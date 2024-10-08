"""Spotify client for handling connections with Spotify."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import metadata
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Self

from aiohttp import ClientSession
from aiohttp.hdrs import METH_GET, METH_POST, METH_PUT
from yarl import URL

from spotifyaio.exceptions import SpotifyConnectionError
from spotifyaio.models import (
    Album,
    Artist,
    ArtistResponse,
    BasePlaylist,
    BaseUserProfile,
    CategoriesResponse,
    Category,
    CategoryPlaylistResponse,
    CurrentPlaying,
    Device,
    Devices,
    Episode,
    FeaturedPlaylistResponse,
    NewReleasesResponse,
    NewReleasesResponseInner,
    PlaybackState,
    PlayedTrack,
    PlayedTrackResponse,
    Playlist,
    PlaylistResponse,
    RepeatMode,
    SavedAlbum,
    SavedAlbumResponse,
    SavedShow,
    SavedShowResponse,
    SavedTrack,
    SavedTrackResponse,
    Show,
    ShowEpisodesResponse,
    SimplifiedEpisode,
    TopArtistsResponse,
    TopTracksResponse,
    UserProfile,
)

if TYPE_CHECKING:
    from spotifyaio import SimplifiedAlbum, Track

VERSION = metadata.version(__package__)


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
        url = URL.build(
            scheme="https",
            host=self.api_host,
            port=443,
        ).joinpath(uri)

        await self.refresh_token()

        headers = {
            "User-Agent": f"AioSpotify/{VERSION}",
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
                    json=data,
                    params=params,
                )
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to Spotify"
            raise SpotifyConnectionError(msg) from exception

        if response.status == 204:
            return ""

        return await response.text()

    async def _get(self, uri: str, params: dict[str, Any] | None = None) -> str:
        """Handle a GET request to Spotify."""
        return await self._request(METH_GET, uri, params=params)

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

    async def get_album(self, album_id: str) -> Album:
        """Get album."""
        identifier = album_id.split(":")[-1]
        response = await self._get(f"v1/albums/{identifier}")
        return Album.from_json(response)

    async def get_artist(self, artist_id: str) -> Artist:
        """Get artist."""
        identifier = artist_id.split(":")[-1]
        response = await self._get(f"v1/artists/{identifier}")
        return Artist.from_json(response)

    async def get_artist_albums(self, artist_id: str) -> list[SimplifiedAlbum]:
        """Get artist albums."""
        params: dict[str, Any] = {"limit": 48}
        identifier = artist_id.split(":")[-1]
        response = await self._get(f"v1/artists/{identifier}/albums", params=params)
        return NewReleasesResponseInner.from_json(response).items

    async def get_playback(self) -> PlaybackState | None:
        """Get playback state."""
        response = await self._get(
            "v1/me/player", params={"additional_types": "track,episode"}
        )
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

    async def add_to_queue(self, uri: str, device_id: str | None = None) -> None:
        """Add to queue."""
        data: dict[str, str] = {"uri": uri}
        if device_id:
            data["device_id"] = device_id
        await self._post("v1/me/player/queue", data=data)

    async def get_playlist(self, playlist_id: str) -> Playlist:
        """Get playlist."""
        identifier = playlist_id.split(":")[-1]
        response = await self._get(f"v1/playlists/{identifier}")
        return Playlist.from_json(response)

    async def get_playlists_for_current_user(self) -> list[BasePlaylist]:
        """Get playlists."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/playlists", params=params)
        return PlaylistResponse.from_json(response).items

    async def get_followed_artists(self) -> list[Artist]:
        """Get followed artists."""
        params: dict[str, Any] = {"limit": 48, "type": "artist"}
        response = await self._get("v1/me/following", params=params)
        return ArtistResponse.from_json(response).artists.items

    async def get_featured_playlists(self) -> list[BasePlaylist]:
        """Get featured playlists."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/browse/featured-playlists", params=params)
        return FeaturedPlaylistResponse.from_json(response).playlists.items

    async def get_category(self, category_id: str) -> Category:
        """Get category."""
        response = await self._get(f"v1/browse/categories/{category_id}")
        return Category.from_json(response)

    async def get_categories(self) -> list[Category]:
        """Get category."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/browse/categories", params=params)
        return CategoriesResponse.from_json(response).categories.items

    async def get_saved_albums(self) -> list[SavedAlbum]:
        """Get saved albums."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/albums", params=params)
        return SavedAlbumResponse.from_json(response).items

    async def get_saved_tracks(self) -> list[SavedTrack]:
        """Get saved tracks."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/tracks", params=params)
        return SavedTrackResponse.from_json(response).items

    async def get_saved_shows(self) -> list[SavedShow]:
        """Get saved shows."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/shows", params=params)
        return SavedShowResponse.from_json(response).items

    async def get_show_episodes(self, show_id: str) -> list[SimplifiedEpisode]:
        """Get show episodes."""
        identifier = show_id.split(":")[-1]
        params: dict[str, Any] = {"limit": 48}
        response = await self._get(f"v1/shows/{identifier}/episodes", params=params)
        return ShowEpisodesResponse.from_json(response).items

    async def get_recently_played_tracks(self) -> list[PlayedTrack]:
        """Get recently played tracks."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/player/recently-played", params=params)
        return PlayedTrackResponse.from_json(response).items

    async def get_category_playlists(self, category_id: str) -> list[BasePlaylist]:
        """Get category playlists."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get(
            f"v1/browse/categories/{category_id}/playlists",
            params=params,
        )
        return CategoryPlaylistResponse.from_json(response).playlists.items

    async def get_new_releases(self) -> list[SimplifiedAlbum]:
        """Get new releases."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/browse/new-releases", params=params)
        return NewReleasesResponse.from_json(response).albums.items

    async def get_top_artists(self) -> list[Artist]:
        """Get top artists."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/top/artists", params=params)
        return TopArtistsResponse.from_json(response).items

    async def get_top_tracks(self) -> list[Track]:
        """Get top tracks."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/top/tracks", params=params)
        return TopTracksResponse.from_json(response).items

    async def get_episode(self, episode_id: str) -> Episode:
        """Get episode."""
        identifier = episode_id.split(":")[-1]
        response = await self._get(f"v1/episodes/{identifier}")
        return Episode.from_json(response)

    async def get_show(self, show_id: str) -> Show:
        """Get show."""
        identifier = show_id.split(":")[-1]
        response = await self._get(f"v1/shows/{identifier}")
        return Show.from_json(response)

    async def get_current_user(self) -> UserProfile:
        """Get current user."""
        response = await self._get("v1/me")
        return UserProfile.from_json(response)

    async def get_user(self, user_id: str) -> BaseUserProfile:
        """Get user."""
        response = await self._get(f"v1/users/{user_id}")
        return BaseUserProfile.from_json(response)

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
