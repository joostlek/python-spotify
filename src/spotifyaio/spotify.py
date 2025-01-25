"""Spotify client for handling connections with Spotify."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import metadata
from typing import TYPE_CHECKING, Any, Callable, Self

from aiohttp import ClientSession
from aiohttp.hdrs import METH_DELETE, METH_GET, METH_POST, METH_PUT
from mashumaro.codecs.json import JSONDecoder
import orjson
from yarl import URL

from spotifyaio.exceptions import SpotifyConnectionError, SpotifyNotFoundError
from spotifyaio.models import (
    Album,
    AlbumsResponse,
    AlbumTracksResponse,
    Artist,
    ArtistResponse,
    ArtistTopTracksResponse,
    Audiobook,
    AudiobookChapterResponse,
    AudiobooksResponse,
    AudioFeatures,
    BasePlaylist,
    BaseUserProfile,
    CategoriesResponse,
    Category,
    CategoryPlaylistResponse,
    Chapter,
    ChaptersResponse,
    CurrentPlaying,
    Device,
    Devices,
    Episode,
    EpisodesResponse,
    FeaturedPlaylistResponse,
    FollowedArtistResponse,
    FollowType,
    Image,
    ModifyPlaylistResponse,
    NewReleasesResponse,
    NewReleasesResponseInner,
    PlaybackState,
    PlayedTrack,
    PlayedTrackResponse,
    Playlist,
    PlaylistResponse,
    PlaylistTrack,
    PlaylistTrackResponse,
    RepeatMode,
    SavedAlbum,
    SavedAlbumResponse,
    SavedAudiobookResponse,
    SavedEpisode,
    SavedEpisodeResponse,
    SavedShow,
    SavedShowResponse,
    SavedTrack,
    SavedTrackResponse,
    SearchResult,
    SearchType,
    Show,
    ShowEpisodesResponse,
    SimplifiedAudiobook,
    SimplifiedChapter,
    SimplifiedEpisode,
    TopArtistsResponse,
    TopTracksResponse,
    UserProfile,
)
from spotifyaio.util import get_identifier

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from spotifyaio import SimplifiedAlbum, SimplifiedTrack, Track

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

        text = await response.text()

        if '"status": 404' in text:
            msg = f"Resource not found: {uri}"
            raise SpotifyNotFoundError(msg)

        return text

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

    async def _delete(
        self,
        uri: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Handle a DELETE request to Spotify."""
        return await self._request(METH_DELETE, uri, data=data, params=params)

    async def get_album(self, album_id: str) -> Album:
        """Get album."""
        identifier = get_identifier(album_id)
        response = await self._get(f"v1/albums/{identifier}")
        return Album.from_json(response)

    async def get_albums(self, album_ids: list[str]) -> list[Album]:
        """Get albums."""
        if not album_ids:
            return []
        if len(album_ids) > 20:
            msg = "Maximum of 20 albums can be requested at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in album_ids])
        }
        response = await self._get("v1/albums", params=params)
        return AlbumsResponse.from_json(response).albums

    async def get_album_tracks(self, album_id: str) -> list[SimplifiedTrack]:
        """Get album tracks."""
        identifier = get_identifier(album_id)
        params: dict[str, Any] = {"limit": 48}
        response = await self._get(f"v1/albums/{identifier}/tracks", params=params)
        return AlbumTracksResponse.from_json(response).items

    async def get_saved_albums(self) -> list[SavedAlbum]:
        """Get saved albums."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/albums", params=params)
        return SavedAlbumResponse.from_json(response).items

    async def save_albums(self, album_ids: list[str]) -> None:
        """Save albums."""
        if not album_ids:
            return
        if len(album_ids) > 50:
            msg = "Maximum of 50 albums can be saved at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in album_ids])
        }
        await self._put("v1/me/albums", params=params)

    async def remove_saved_albums(self, album_ids: list[str]) -> None:
        """Remove saved albums."""
        if not album_ids:
            return
        if len(album_ids) > 50:
            msg = "Maximum of 50 albums can be removed at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in album_ids])
        }
        await self._delete("v1/me/albums", params=params)

    async def are_albums_saved(self, album_ids: list[str]) -> dict[str, bool]:
        """Check if albums are saved."""
        if not album_ids:
            return {}
        if len(album_ids) > 20:
            msg = "Maximum of 20 albums can be checked at once"
            raise ValueError(msg)
        identifiers = [get_identifier(i) for i in album_ids]
        params: dict[str, Any] = {"ids": ",".join(identifiers)}
        response = await self._get("v1/me/albums/contains", params=params)
        body: list[bool] = orjson.loads(response)  # pylint: disable=no-member
        return dict(zip(identifiers, body))

    async def get_new_releases(self) -> list[SimplifiedAlbum]:
        """Get new releases."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/browse/new-releases", params=params)
        return NewReleasesResponse.from_json(response).albums.items

    async def get_artist(self, artist_id: str) -> Artist:
        """Get artist."""
        identifier = artist_id.split(":")[-1]
        response = await self._get(f"v1/artists/{identifier}")
        return Artist.from_json(response)

    async def get_artists(self, artist_ids: list[str]) -> list[Artist]:
        """Get several artists."""
        if not artist_ids:
            return []
        if len(artist_ids) > 50:
            msg = "Maximum of 50 artists can be requested at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in artist_ids])
        }
        response = await self._get("v1/artists", params=params)
        return ArtistResponse.from_json(response).artists

    async def get_artist_albums(self, artist_id: str) -> list[SimplifiedAlbum]:
        """Get artist albums."""
        params: dict[str, Any] = {"limit": 48}
        identifier = artist_id.split(":")[-1]
        response = await self._get(f"v1/artists/{identifier}/albums", params=params)
        return NewReleasesResponseInner.from_json(response).items

    async def get_artist_top_tracks(self, artist_id: str) -> list[Track]:
        """Get artist top tracks."""
        identifier = artist_id.split(":")[-1]
        response = await self._get(f"v1/artists/{identifier}/top-tracks")
        return ArtistTopTracksResponse.from_json(response).tracks

    async def get_audiobook(self, audiobook_id: str) -> Audiobook:
        """Get audiobook."""
        identifier = get_identifier(audiobook_id)
        response = await self._get(f"v1/audiobooks/{identifier}")
        return Audiobook.from_json(response)

    async def get_audiobooks(self, audiobook_ids: list[str]) -> list[Audiobook]:
        """Get audiobooks."""
        identifiers = [get_identifier(i) for i in audiobook_ids]
        params: dict[str, Any] = {"ids": ",".join(identifiers)}
        response = await self._get("v1/audiobooks", params=params)
        return AudiobooksResponse.from_json(response).audiobooks

    async def get_audiobook_chapters(
        self, audiobook_id: str
    ) -> list[SimplifiedChapter]:
        """Get audiobook chapters."""
        identifier = get_identifier(audiobook_id)
        params: dict[str, Any] = {"limit": 50}
        response = await self._get(
            f"v1/audiobooks/{identifier}/chapters", params=params
        )
        return AudiobookChapterResponse.from_json(response).items

    async def get_saved_audiobooks(self) -> list[SimplifiedAudiobook]:
        """Get saved audiobooks."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/audiobooks", params=params)
        return SavedAudiobookResponse.from_json(response).items

    async def save_audiobooks(self, audiobook_ids: list[str]) -> None:
        """Save audiobooks."""
        if not audiobook_ids:
            return
        if len(audiobook_ids) > 50:
            msg = "Maximum of 50 audiobooks can be saved at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in audiobook_ids])
        }
        await self._put("v1/me/audiobooks", params=params)

    async def remove_saved_audiobooks(self, audiobook_ids: list[str]) -> None:
        """Remove saved audiobooks."""
        if not audiobook_ids:
            return
        if len(audiobook_ids) > 50:
            msg = "Maximum of 50 audiobooks can be removed at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in audiobook_ids])
        }
        await self._delete("v1/me/audiobooks", params=params)

    async def are_audiobooks_saved(self, audiobook_ids: list[str]) -> dict[str, bool]:
        """Check if audiobooks are saved."""
        if not audiobook_ids:
            return {}
        if len(audiobook_ids) > 50:
            msg = "Maximum of 50 audiobooks can be checked at once"
            raise ValueError(msg)
        identifiers = [get_identifier(i) for i in audiobook_ids]
        params: dict[str, Any] = {"ids": ",".join(identifiers)}
        response = await self._get("v1/me/audiobooks/contains", params=params)
        body: list[bool] = orjson.loads(response)  # pylint: disable=no-member
        return dict(zip(identifiers, body))

    async def get_categories(self) -> list[Category]:
        """Get list of categories."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/browse/categories", params=params)
        return CategoriesResponse.from_json(response).categories.items

    async def get_category(self, category_id: str) -> Category:
        """Get category."""
        response = await self._get(f"v1/browse/categories/{category_id}")
        return Category.from_json(response)

    async def get_chapter(self, chapter_id: str) -> Chapter:
        """Get chapter."""
        identifier = chapter_id.split(":")[-1]
        response = await self._get(f"v1/chapters/{identifier}")
        return Chapter.from_json(response)

    async def get_chapters(self, chapter_ids: list[str]) -> list[Chapter]:
        """Get chapters."""
        if not chapter_ids:
            return []
        if len(chapter_ids) > 50:
            msg = "Maximum of 50 chapters can be requested at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in chapter_ids])
        }
        response = await self._get("v1/chapters", params=params)
        return ChaptersResponse.from_json(response).chapters

    async def get_episode(self, episode_id: str) -> Episode:
        """Get episode."""
        identifier = episode_id.split(":")[-1]
        response = await self._get(f"v1/episodes/{identifier}")
        return Episode.from_json(response)

    async def get_episodes(self, episode_ids: list[str]) -> list[Episode]:
        """Get episodes."""
        if not episode_ids:
            return []
        if len(episode_ids) > 50:
            msg = "Maximum of 50 episodes can be requested at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in episode_ids])
        }
        response = await self._get("v1/episodes", params=params)
        return EpisodesResponse.from_json(response).episodes

    async def get_saved_episodes(self) -> list[SavedEpisode]:
        """Get saved episodes."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/episodes", params=params)
        return SavedEpisodeResponse.from_json(response).items

    async def save_episodes(self, episode_ids: list[str]) -> None:
        """Save episodes."""
        if not episode_ids:
            return
        if len(episode_ids) > 50:
            msg = "Maximum of 50 episodes can be saved at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in episode_ids])
        }
        await self._put("v1/me/episodes", params=params)

    async def remove_saved_episodes(self, episode_ids: list[str]) -> None:
        """Remove saved episodes."""
        if not episode_ids:
            return
        if len(episode_ids) > 50:
            msg = "Maximum of 50 episodes can be removed at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in episode_ids])
        }
        await self._delete("v1/me/episodes", params=params)

    async def are_episodes_saved(self, episode_ids: list[str]) -> dict[str, bool]:
        """Check if episodes are saved."""
        if not episode_ids:
            return {}
        if len(episode_ids) > 50:
            msg = "Maximum of 50 episodes can be checked at once"
            raise ValueError(msg)
        identifiers = [get_identifier(i) for i in episode_ids]
        params: dict[str, Any] = {"ids": ",".join(identifiers)}
        response = await self._get("v1/me/episodes/contains", params=params)
        body: list[bool] = orjson.loads(response)  # pylint: disable=no-member
        return dict(zip(identifiers, body))

    async def get_playback(self) -> PlaybackState | None:
        """Get playback state."""
        response = await self._get(
            "v1/me/player", params={"additional_types": "track,episode"}
        )
        if response == "":
            return None
        return PlaybackState.from_json(response)

    async def transfer_playback(self, device_id: str) -> None:
        """Transfer playback."""
        await self._put("v1/me/player", {"device_ids": [device_id]})

    async def get_devices(self) -> list[Device]:
        """Get devices."""
        response = await self._get("v1/me/player/devices")
        return Devices.from_json(response).devices

    async def get_current_playing(self) -> CurrentPlaying | None:
        """Get playback state."""
        response = await self._get("v1/me/player/currently-playing")
        if response == "":
            return None
        return CurrentPlaying.from_json(response)

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

    async def get_recently_played_tracks(self) -> list[PlayedTrack]:
        """Get recently played tracks."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/player/recently-played", params=params)
        return PlayedTrackResponse.from_json(response).items

    # Get queue

    async def add_to_queue(self, uri: str, device_id: str | None = None) -> None:
        """Add to queue."""
        data: dict[str, str] = {"uri": uri}
        if device_id:
            data["device_id"] = device_id
        await self._post("v1/me/player/queue", data=data)

    async def get_playlist(self, playlist_id: str) -> Playlist:
        """Get playlist."""
        identifier = playlist_id.split(":")[-1]
        response = await self._get(
            f"v1/playlists/{identifier}", params={"additional_types": "track,episode"}
        )
        return Playlist.from_json(response)

    async def update_playlist_details(
        self,
        playlist_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        public: bool | None = None,
        collaborative: bool | None = None,
    ) -> None:
        """Update playlist details."""
        identifier = get_identifier(playlist_id)
        data: dict[str, Any] = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if public is not None:
            data["public"] = public
        if collaborative is not None:
            data["collaborative"] = collaborative
        await self._put(f"v1/playlists/{identifier}", data=data)

    async def get_playlist_items(self, playlist_id: str) -> list[PlaylistTrack]:
        """Get playlist tracks."""
        identifier = get_identifier(playlist_id)
        params: dict[str, Any] = {"limit": 48}
        response = await self._get(f"v1/playlists/{identifier}/tracks", params=params)
        return PlaylistTrackResponse.from_json(response).items

    async def update_playlist_items(
        self,
        playlist_id: str,
        uris: list[str],
        *,
        range_start: int | None = None,
        insert_before: int | None = None,
        range_length: int | None = None,
        snapshot_id: str | None = None,
    ) -> str:
        """Update playlist tracks."""
        identifier = get_identifier(playlist_id)
        data: dict[str, Any] = {"uris": uris}
        if range_start is not None:
            data["range_start"] = range_start
        if insert_before is not None:
            data["insert_before"] = insert_before
        if range_length is not None:
            data["range_length"] = range_length
        if snapshot_id:
            data["snapshot_id"] = snapshot_id
        response = await self._put(f"v1/playlists/{identifier}/tracks", data=data)
        return ModifyPlaylistResponse.from_json(response).snapshot_id

    async def add_playlist_items(
        self,
        playlist_id: str,
        uris: list[str],
        position: int | None = None,
    ) -> str:
        """Add playlist tracks."""
        if len(uris) > 100:
            msg = "Maximum of 100 tracks can be added at once"
            raise ValueError(msg)
        identifier = get_identifier(playlist_id)
        data: dict[str, Any] = {"uris": uris}
        if position is not None:
            data["position"] = position
        response = await self._post(f"v1/playlists/{identifier}/tracks", data=data)
        return ModifyPlaylistResponse.from_json(response).snapshot_id

    async def remove_playlist_items(
        self,
        playlist_id: str,
        uris: list[str],
        snapshot_id: str | None = None,
    ) -> str:
        """Remove playlist tracks."""
        if len(uris) > 100:
            msg = "Maximum of 100 tracks can be removed at once"
            raise ValueError(msg)
        identifier = get_identifier(playlist_id)
        data: dict[str, Any] = {"tracks": [{"uri": uri} for uri in uris]}
        if snapshot_id:
            data["snapshot_id"] = snapshot_id
        response = await self._delete(f"v1/playlists/{identifier}/tracks", data=data)
        return ModifyPlaylistResponse.from_json(response).snapshot_id

    async def get_playlists_for_current_user(self) -> list[BasePlaylist]:
        """Get playlists."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/playlists", params=params)
        return PlaylistResponse.from_json(response).items

    async def get_playlists_for_user(self, user_id: str) -> list[BasePlaylist]:
        """Get playlists."""
        identifier = get_identifier(user_id)
        params: dict[str, Any] = {"limit": 48}
        response = await self._get(f"v1/user/{identifier}/playlists", params=params)
        return PlaylistResponse.from_json(response).items

    async def create_playlist(
        self,
        user_id: str,
        name: str,
        *,
        description: str | None = None,
        public: bool | None = None,
        collaborative: bool | None = None,
    ) -> Playlist:
        """Create playlist."""
        identifier = get_identifier(user_id)
        data: dict[str, Any] = {"name": name}
        if description:
            data["description"] = description
        if public is not None:
            data["public"] = public
        if collaborative is not None:
            data["collaborative"] = collaborative
        response = await self._post(f"v1/users/{identifier}/playlists", data=data)
        return Playlist.from_json(response)

    async def get_featured_playlists(self) -> list[BasePlaylist]:
        """Get featured playlists."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/browse/featured-playlists", params=params)
        return FeaturedPlaylistResponse.from_json(response).playlists.items

    async def get_category_playlists(self, category_id: str) -> list[BasePlaylist]:
        """Get category playlists."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get(
            f"v1/browse/categories/{category_id}/playlists",
            params=params,
        )
        return CategoryPlaylistResponse.from_json(response).playlists.items

    async def get_playlist_cover_image(self, playlist_id: str) -> list[Image]:
        """Get playlist cover image."""
        identifier = get_identifier(playlist_id)
        response = await self._get(f"v1/playlists/{identifier}/images")
        return JSONDecoder(list[Image]).decode(response)

    # Upload a custom playlist cover image

    async def search(
        self, query: str, types: list[SearchType], *, limit: int = 48
    ) -> SearchResult:
        """Search."""
        params: dict[str, Any] = {"q": query, "limit": limit, "type": ",".join(types)}
        response = await self._get("v1/search", params=params)
        return SearchResult.from_json(response)

    async def get_show(self, show_id: str) -> Show:
        """Get show."""
        identifier = show_id.split(":")[-1]
        response = await self._get(f"v1/shows/{identifier}")
        return Show.from_json(response)

    # Get several shows

    async def get_show_episodes(self, show_id: str) -> list[SimplifiedEpisode]:
        """Get show episodes."""
        identifier = show_id.split(":")[-1]
        params: dict[str, Any] = {"limit": 48}
        response = await self._get(f"v1/shows/{identifier}/episodes", params=params)
        return ShowEpisodesResponse.from_json(response).items

    async def get_saved_shows(self) -> list[SavedShow]:
        """Get saved shows."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/shows", params=params)
        return SavedShowResponse.from_json(response).items

    async def save_shows(self, show_ids: list[str]) -> None:
        """Save shows."""
        if not show_ids:
            return
        if len(show_ids) > 50:
            msg = "Maximum of 50 shows can be saved at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in show_ids])
        }
        await self._put("v1/me/shows", params=params)

    async def remove_saved_shows(self, show_ids: list[str]) -> None:
        """Remove saved shows."""
        if not show_ids:
            return
        if len(show_ids) > 50:
            msg = "Maximum of 50 shows can be removed at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in show_ids])
        }
        await self._delete("v1/me/shows", params=params)

    async def are_shows_saved(self, show_ids: list[str]) -> dict[str, bool]:
        """Check if shows are saved."""
        if not show_ids:
            return {}
        if len(show_ids) > 50:
            msg = "Maximum of 50 shows can be checked at once"
            raise ValueError(msg)
        identifiers = [get_identifier(i) for i in show_ids]
        params: dict[str, Any] = {"ids": ",".join(identifiers)}
        response = await self._get("v1/me/shows/contains", params=params)
        body: list[bool] = orjson.loads(response)  # pylint: disable=no-member
        return dict(zip(identifiers, body))

    # Get a track

    # Get several tracks

    async def get_saved_tracks(self) -> list[SavedTrack]:
        """Get saved tracks."""
        params: dict[str, Any] = {"limit": 48}
        response = await self._get("v1/me/tracks", params=params)
        return SavedTrackResponse.from_json(response).items

    async def save_tracks(self, track_ids: list[str]) -> None:
        """Save tracks."""
        if not track_ids:
            return
        if len(track_ids) > 50:
            msg = "Maximum of 50 tracks can be saved at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in track_ids])
        }
        await self._put("v1/me/tracks", params=params)

    async def remove_saved_tracks(self, track_ids: list[str]) -> None:
        """Remove saved tracks."""
        if not track_ids:
            return
        if len(track_ids) > 50:
            msg = "Maximum of 50 tracks can be removed at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "ids": ",".join([get_identifier(i) for i in track_ids])
        }
        await self._delete("v1/me/tracks", params=params)

    async def are_tracks_saved(self, track_ids: list[str]) -> dict[str, bool]:
        """Check if tracks are saved."""
        if not track_ids:
            return {}
        if len(track_ids) > 50:
            msg = "Maximum of 50 tracks can be checked at once"
            raise ValueError(msg)
        identifiers = [get_identifier(i) for i in track_ids]
        params: dict[str, Any] = {"ids": ",".join(identifiers)}
        response = await self._get("v1/me/tracks/contains", params=params)
        body: list[bool] = orjson.loads(response)  # pylint: disable=no-member
        return dict(zip(identifiers, body))

    async def get_audio_features(self, track_id: str) -> AudioFeatures:
        """Get audio features."""
        identifier = get_identifier(track_id)
        response = await self._get(f"v1/audio-features/{identifier}")
        return AudioFeatures.from_json(response)

    async def get_current_user(self) -> UserProfile:
        """Get current user."""
        response = await self._get("v1/me")
        return UserProfile.from_json(response)

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

    async def get_user(self, user_id: str) -> BaseUserProfile:
        """Get user."""
        response = await self._get(f"v1/users/{user_id}")
        return BaseUserProfile.from_json(response)

    async def follow_playlist(self, playlist_id: str) -> None:
        """Follow a playlist."""
        identifier = get_identifier(playlist_id)
        await self._put(f"v1/playlists/{identifier}/followers")

    async def unfollow_playlist(self, playlist_id: str) -> None:
        """Unfollow a playlist."""
        identifier = get_identifier(playlist_id)
        await self._delete(f"v1/playlists/{identifier}/followers")

    async def get_followed_artists(self) -> list[Artist]:
        """Get followed artists."""
        params: dict[str, Any] = {"limit": 48, "type": "artist"}
        response = await self._get("v1/me/following", params=params)
        return FollowedArtistResponse.from_json(response).artists.items

    async def follow_account(self, follow_type: FollowType, ids: list[str]) -> None:
        """Follow an artist or user."""
        if not ids:
            return
        if len(ids) > 50:
            msg = "Maximum of 50 accounts can be followed at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "type": follow_type,
            "ids": ",".join([get_identifier(i) for i in ids]),
        }
        await self._put("v1/me/following", params=params)

    async def unfollow_account(self, follow_type: FollowType, ids: list[str]) -> None:
        """Unfollow an artist or user."""
        if not ids:
            return
        if len(ids) > 50:
            msg = "Maximum of 50 accounts can be unfollowed at once"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "type": follow_type,
            "ids": ",".join([get_identifier(i) for i in ids]),
        }
        await self._delete("v1/me/following", params=params)

    async def are_accounts_followed(
        self, follow_type: FollowType, ids: list[str]
    ) -> dict[str, bool]:
        """Check if artists or users are followed."""
        if not ids:
            return {}
        if len(ids) > 50:
            msg = "Maximum of 50 accounts can be checked at once"
            raise ValueError(msg)
        identifiers = [get_identifier(i) for i in ids]
        params: dict[str, Any] = {"type": follow_type, "ids": ",".join(identifiers)}
        response = await self._get("v1/me/following/contains", params=params)
        body: list[bool] = orjson.loads(response)  # pylint: disable=no-member
        return dict(zip(identifiers, body))

    async def is_following_playlist(self, playlist_id: str) -> bool:
        """Check if playlist is followed."""
        identifier = get_identifier(playlist_id)
        response = await self._get(f"v1/playlists/{identifier}/followers/contains")
        return bool(orjson.loads(response)[0])  # pylint: disable=no-member

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
