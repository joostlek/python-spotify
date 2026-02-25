"""Asynchronous Python client for Spotify."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aiohttp
from aiohttp.hdrs import METH_DELETE, METH_GET, METH_POST, METH_PUT
from aioresponses import CallbackResult, aioresponses
import pytest
from yarl import URL

from spotifyaio import (
    RepeatMode,
    SpotifyClient,
    SpotifyConnectionError,
    SpotifyError,
    SpotifyNotFoundError,
)
from spotifyaio.models import SearchType

from . import load_fixture
from .const import HEADERS, SPOTIFY_URL

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion


async def test_putting_in_own_session(
    responses: aioresponses,
) -> None:
    """Test putting in own session."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player?additional_types=track,episode",
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
        f"{SPOTIFY_URL}/v1/me/player?additional_types=track,episode",
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


async def test_json_decode_error(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test raising a JSON decode error."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player?additional_types=track,episode",
        status=200,
        body="<>",
    )
    with pytest.raises(SpotifyError):
        assert await authenticated_client.get_playback()


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
        f"{SPOTIFY_URL}/v1/me/player?additional_types=track,episode",
        callback=response_handler,
    )
    async with SpotifyClient(request_timeout=1) as spotify:
        with pytest.raises(SpotifyConnectionError):
            assert await spotify.get_playback()


async def test_get_album_tracks(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving tracks of an album."""
    responses.get(
        f"{SPOTIFY_URL}/v1/albums/4aawyAB9vmqN3uQ7FjRGTy/tracks?limit=48",
        status=200,
        body=load_fixture("album_tracks.json"),
    )
    response = await authenticated_client.get_album_tracks("4aawyAB9vmqN3uQ7FjRGTy")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/albums/4aawyAB9vmqN3uQ7FjRGTy/tracks",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


@pytest.mark.parametrize(
    "playback_fixture",
    [
        "playback_1.json",
        "playback_2.json",
        "playback_3.json",
        "playback_4.json",
        "playback_episode_1.json",
        "playback_audiobook_1.json",
    ],
)
async def test_get_playback_state(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    playback_fixture: str,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player?additional_types=track,episode",
        status=200,
        body=load_fixture(playback_fixture),
    )
    response = await authenticated_client.get_playback()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player",
        METH_GET,
        headers=HEADERS,
        params={"additional_types": "track,episode"},
        json=None,
    )


async def test_get_no_playback_state(
    authenticated_client: SpotifyClient,
    responses: aioresponses,
) -> None:
    """Test retrieving no playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player?additional_types=track,episode",
        status=204,
    )
    response = await authenticated_client.get_playback()
    assert response is None
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player",
        METH_GET,
        headers=HEADERS,
        params={"additional_types": "track,episode"},
        json=None,
    )


async def test_transfer_playback(
    authenticated_client: SpotifyClient,
    responses: aioresponses,
) -> None:
    """Test transferring playback."""
    responses.put(
        f"{SPOTIFY_URL}/v1/me/player", status=200, body="3o0RYoo5iOMKSmEbunsbvW"
    )
    await authenticated_client.transfer_playback("test")
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player",
        METH_PUT,
        headers=HEADERS,
        json={"device_ids": ["test"]},
        params=None,
    )


async def test_get_devices(
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
    responses: aioresponses,
) -> None:
    """Test retrieving devices."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player/devices",
        status=200,
        body=load_fixture("devices.json"),
    )
    devices = await authenticated_client.get_devices()
    assert devices == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/devices",
        headers=HEADERS,
        json=None,
        params=None,
    )


async def test_get_current_playing(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving current playing."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player/currently-playing",
        status=200,
        body=load_fixture("current_playing_track.json"),
    )
    response = await authenticated_client.get_current_playing()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/currently-playing",
        headers=HEADERS,
        json=None,
        params=None,
    )


async def test_get_no_current_playing_state(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving no current playing state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player/currently-playing",
        status=204,
    )
    response = await authenticated_client.get_current_playing()
    assert response is None
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/currently-playing",
        headers=HEADERS,
        params=None,
        json=None,
    )


@pytest.mark.parametrize(
    ("arguments", "expected_params", "expected_data"),
    [
        ({}, {}, {"position_ms": 0}),
        ({"device_id": "123qwe"}, {"device_id": "123qwe"}, {"position_ms": 0}),
        (
            {"context_uri": "spotify:artist:6cmp7ut7okJAgJOSaMAVf3"},
            {},
            {"position_ms": 0, "context_uri": "spotify:artist:6cmp7ut7okJAgJOSaMAVf3"},
        ),
        (
            {
                "uris": [
                    "spotify:track:1FyXbzOlq3dkxaB6iRsETv",
                    "spotify:track:4e9hUiLsN4mx61ARosFi7p",
                ],
                "uri_offset": "spotify:track:4e9hUiLsN4mx61ARosFi7p",
            },
            {},
            {
                "position_ms": 0,
                "uris": [
                    "spotify:track:1FyXbzOlq3dkxaB6iRsETv",
                    "spotify:track:4e9hUiLsN4mx61ARosFi7p",
                ],
                "offset": {"uri": "spotify:track:4e9hUiLsN4mx61ARosFi7p"},
            },
        ),
        (
            {"uris": ["spotify:artist:6cmp7ut7okJAgJOSaMAVf3"], "position_offset": 5},
            {},
            {
                "position_ms": 0,
                "uris": ["spotify:artist:6cmp7ut7okJAgJOSaMAVf3"],
                "offset": {"position": 5},
            },
        ),
        ({"position": 5000}, {}, {"position_ms": 5000}),
    ],
)
async def test_resume_playback(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    arguments: dict[str, Any],
    expected_params: dict[str, Any],
    expected_data: dict[str, Any],
) -> None:
    """Test resuming playback."""
    url = URL.build(
        scheme="https",
        host="api.spotify.com",
        port=443,
        path="/v1/me/player/play",
        query=expected_params,
    )
    responses.put(url, status=200, body="3o0RYoo5iOMKSmEbunsbvW")
    await authenticated_client.start_playback(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/play",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        json=expected_data,
    )


@pytest.mark.parametrize(
    ("arguments", "expected_params"),
    [
        ({}, {}),
        ({"device_id": "123qwe"}, {"device_id": "123qwe"}),
    ],
)
async def test_pause_playback(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    arguments: dict[str, Any],
    expected_params: dict[str, Any],
) -> None:
    """Test pausing playback."""
    url = URL.build(
        scheme="https",
        host="api.spotify.com",
        port=443,
        path="/v1/me/player/pause",
        query=expected_params,
    )
    responses.put(url, status=200, body="3o0RYoo5iOMKSmEbunsbvW")
    await authenticated_client.pause_playback(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/pause",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        json=None,
    )


@pytest.mark.parametrize(
    ("arguments", "expected_params"),
    [
        ({}, {}),
        ({"device_id": "123qwe"}, {"device_id": "123qwe"}),
    ],
)
async def test_next_track(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    arguments: dict[str, Any],
    expected_params: dict[str, Any],
) -> None:
    """Test next track."""
    url = URL.build(
        scheme="https",
        host="api.spotify.com",
        port=443,
        path="/v1/me/player/next",
        query=expected_params,
    )
    responses.post(url, status=200, body="3o0RYoo5iOMKSmEbunsbvW")
    await authenticated_client.next_track(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/next",
        METH_POST,
        headers=HEADERS,
        params=expected_params,
        json=None,
    )


@pytest.mark.parametrize(
    ("arguments", "expected_params"),
    [
        ({}, {}),
        ({"device_id": "123qwe"}, {"device_id": "123qwe"}),
    ],
)
async def test_previous_track(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    arguments: dict[str, Any],
    expected_params: dict[str, Any],
) -> None:
    """Test previous track."""
    url = URL.build(
        scheme="https",
        host="api.spotify.com",
        port=443,
        path="/v1/me/player/previous",
        query=expected_params,
    )
    responses.post(url, status=200, body="3o0RYoo5iOMKSmEbunsbvW")
    await authenticated_client.previous_track(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/previous",
        METH_POST,
        headers=HEADERS,
        params=expected_params,
        json=None,
    )


@pytest.mark.parametrize(
    ("arguments", "expected_params"),
    [
        ({"position": 5000}, {"position_ms": 5000}),
        (
            {"position": 5000, "device_id": "123qwe"},
            {"device_id": "123qwe", "position_ms": 5000},
        ),
    ],
)
async def test_seek_track(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    arguments: dict[str, Any],
    expected_params: dict[str, Any],
) -> None:
    """Test seeking track."""
    url = URL.build(
        scheme="https",
        host="api.spotify.com",
        port=443,
        path="/v1/me/player/seek",
        query=expected_params,
    )
    responses.put(url, status=200, body="3o0RYoo5iOMKSmEbunsbvW")
    await authenticated_client.seek_track(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/seek",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        json=None,
    )


@pytest.mark.parametrize(
    ("arguments", "expected_params"),
    [
        ({"state": RepeatMode.OFF}, {"state": "off"}),
        ({"state": RepeatMode.TRACK}, {"state": "track"}),
        ({"state": RepeatMode.CONTEXT}, {"state": "context"}),
        (
            {"state": RepeatMode.CONTEXT, "device_id": "123qwe"},
            {"state": "context", "device_id": "123qwe"},
        ),
    ],
)
async def test_set_repeat(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    arguments: dict[str, Any],
    expected_params: dict[str, Any],
) -> None:
    """Test setting repeat."""
    url = URL.build(
        scheme="https",
        host="api.spotify.com",
        port=443,
        path="/v1/me/player/repeat",
        query=expected_params,
    )
    responses.put(url, status=200, body="3o0RYoo5iOMKSmEbunsbvW")
    await authenticated_client.set_repeat(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/repeat",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        json=None,
    )


@pytest.mark.parametrize(
    ("arguments", "expected_params"),
    [
        ({"volume": 50}, {"volume_percent": 50}),
        (
            {"volume": 50, "device_id": "123qwe"},
            {"volume_percent": 50, "device_id": "123qwe"},
        ),
    ],
)
async def test_set_volume(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    arguments: dict[str, Any],
    expected_params: dict[str, Any],
) -> None:
    """Test setting volume."""
    url = URL.build(
        scheme="https",
        host="api.spotify.com",
        port=443,
        path="/v1/me/player/volume",
        query=expected_params,
    )
    responses.put(url, status=200, body="3o0RYoo5iOMKSmEbunsbvW")
    await authenticated_client.set_volume(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/volume",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        json=None,
    )


@pytest.mark.parametrize(
    ("arguments", "expected_params"),
    [
        ({"state": True}, {"state": "true"}),
        (
            {"state": False, "device_id": "123qwe"},
            {"state": "false", "device_id": "123qwe"},
        ),
    ],
)
async def test_set_shuffle(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    arguments: dict[str, Any],
    expected_params: dict[str, Any],
) -> None:
    """Test setting shuffle."""
    url = URL.build(
        scheme="https",
        host="api.spotify.com",
        port=443,
        path="/v1/me/player/shuffle",
        query=expected_params,
    )
    responses.put(url, status=200, body="3o0RYoo5iOMKSmEbunsbvW")
    await authenticated_client.set_shuffle(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/shuffle",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        json=None,
    )


@pytest.mark.parametrize(
    ("arguments", "expected_data"),
    [
        (
            {"uri": "spotify:track:1FyXbzOlq3dkxaB6iRsETv"},
            {"uri": "spotify:track:1FyXbzOlq3dkxaB6iRsETv"},
        ),
        (
            {"uri": "spotify:track:1FyXbzOlq3dkxaB6iRsETv", "device_id": "123qwe"},
            {"uri": "spotify:track:1FyXbzOlq3dkxaB6iRsETv", "device_id": "123qwe"},
        ),
    ],
)
async def test_add_to_queue(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    arguments: dict[str, Any],
    expected_data: dict[str, Any],
) -> None:
    """Test adding to queue."""
    responses.post(
        f"{SPOTIFY_URL}/v1/me/player/queue", status=200, body="3o0RYoo5iOMKSmEbunsbvW"
    )
    await authenticated_client.add_to_queue(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/queue",
        METH_POST,
        headers=HEADERS,
        params=None,
        json=expected_data,
    )


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
        json=None,
    )


@pytest.mark.parametrize(
    "fixture",
    [
        "playlist_1.json",
        "playlist_2.json",
        "playlist_3.json",
    ],
)
async def test_get_playlist(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
    fixture: str,
) -> None:
    """Test retrieving playlist."""
    responses.get(
        f"{SPOTIFY_URL}/v1/playlists/1Cp6VQCKf2VL4sP09jN9oX?additional_types=track,episode",
        status=200,
        body=load_fixture(fixture),
    )
    response = await authenticated_client.get_playlist("1Cp6VQCKf2VL4sP09jN9oX")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/1Cp6VQCKf2VL4sP09jN9oX",
        METH_GET,
        headers=HEADERS,
        params={"additional_types": "track,episode"},
        json=None,
    )


async def test_get_not_found_playlist(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving not found playlist."""
    responses.get(
        f"{SPOTIFY_URL}/v1/playlists/1Cp6VQCKf2VL4sP09jN9oX?additional_types=track,episode",
        status=200,
        body=load_fixture("playlist_not_found.json"),
    )
    with pytest.raises(
        SpotifyNotFoundError,
        match="Resource not found: v1/playlists/1Cp6VQCKf2VL4sP09jN9oX",
    ):
        await authenticated_client.get_playlist("1Cp6VQCKf2VL4sP09jN9oX")


@pytest.mark.parametrize(
    "fixture",
    [
        "current_user_playlist_1.json",
        "current_user_playlist_2.json",
    ],
)
async def test_get_current_users_playlists(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
    fixture: str,
) -> None:
    """Test retrieving playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/playlists?limit=48",
        status=200,
        body=load_fixture(fixture),
    )
    response = await authenticated_client.get_playlists_for_current_user()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/playlists",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


@pytest.mark.parametrize(
    "playlist_id",
    [
        "1Cp6VQCKf2VL4sP09jN9oX",
        "spotify:playlist:1Cp6VQCKf2VL4sP09jN9oX",
        "spotify:user:chilledcow:playlist:1Cp6VQCKf2VL4sP09jN9oX",
    ],
)
async def test_get_playlist_variation(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    playlist_id: str,
) -> None:
    """Test retrieving playlist with different inputs."""
    responses.get(
        f"{SPOTIFY_URL}/v1/playlists/1Cp6VQCKf2VL4sP09jN9oX?additional_types=track,episode",
        status=200,
        body=load_fixture("playlist_1.json"),
    )
    await authenticated_client.get_playlist(playlist_id)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/1Cp6VQCKf2VL4sP09jN9oX",
        METH_GET,
        headers=HEADERS,
        params={"additional_types": "track,episode"},
        json=None,
    )


async def test_get_current_user(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving current user."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me",
        status=200,
        body=load_fixture("current_user.json"),
    )
    response = await authenticated_client.get_current_user()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )


async def test_get_episode(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving episode."""
    responses.get(
        f"{SPOTIFY_URL}/v1/episodes/3o0RYoo5iOMKSmEbunsbvW",
        status=200,
        body=load_fixture("episode.json"),
    )
    response = await authenticated_client.get_episode("3o0RYoo5iOMKSmEbunsbvW")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/episodes/3o0RYoo5iOMKSmEbunsbvW",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )


async def test_get_show(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving show."""
    responses.get(
        f"{SPOTIFY_URL}/v1/shows/1Y9ExMgMxoBVrgrfU7u0nD",
        status=200,
        body=load_fixture("show.json"),
    )
    response = await authenticated_client.get_show("1Y9ExMgMxoBVrgrfU7u0nD")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/shows/1Y9ExMgMxoBVrgrfU7u0nD",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )


async def test_get_following_artists(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving show."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/following?type=artist&limit=48",
        status=200,
        body=load_fixture("followed_artists.json"),
    )
    response = await authenticated_client.get_followed_artists()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/following",
        METH_GET,
        headers=HEADERS,
        params={"type": "artist", "limit": 48},
        json=None,
    )


async def test_get_saved_albums(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving saved albums."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/albums?limit=48",
        status=200,
        body=load_fixture("saved_albums.json"),
    )
    response = await authenticated_client.get_saved_albums()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/albums",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_saved_tracks(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving saved tracks."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/tracks?limit=48",
        status=200,
        body=load_fixture("saved_tracks.json"),
    )
    response = await authenticated_client.get_saved_tracks()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/tracks",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_saved_shows(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving saved shows."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/shows?limit=48",
        status=200,
        body=load_fixture("saved_shows.json"),
    )
    response = await authenticated_client.get_saved_shows()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/shows",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_recently_played_tracks(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving recently played tracks."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player/recently-played?limit=48",
        status=200,
        body=load_fixture("recently_played_tracks.json"),
    )
    response = await authenticated_client.get_recently_played_tracks()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/recently-played",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_top_artists(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving top artists."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/top/artists?limit=48",
        status=200,
        body=load_fixture("top_artists.json"),
    )
    response = await authenticated_client.get_top_artists()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/top/artists",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_top_tracks(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving top tracks."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/top/tracks?limit=48",
        status=200,
        body=load_fixture("top_tracks.json"),
    )
    response = await authenticated_client.get_top_tracks()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/top/tracks",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_artist(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving an artist."""
    responses.get(
        f"{SPOTIFY_URL}/v1/artists/0TnOYISbd1XYRBk9myaseg",
        status=200,
        body=load_fixture("artist.json"),
    )
    response = await authenticated_client.get_artist("0TnOYISbd1XYRBk9myaseg")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/artists/0TnOYISbd1XYRBk9myaseg",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )


async def test_get_artist_albums(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving albums of an artist."""
    responses.get(
        f"{SPOTIFY_URL}/v1/artists/0TnOYISbd1XYRBk9myaseg/albums?limit=48",
        status=200,
        body=load_fixture("artist_albums.json"),
    )
    response = await authenticated_client.get_artist_albums("0TnOYISbd1XYRBk9myaseg")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/artists/0TnOYISbd1XYRBk9myaseg/albums",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_audiobook(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving audiobook."""
    responses.get(
        f"{SPOTIFY_URL}/v1/audiobooks/6SJQ8VzM5PlDy11wMtcD6v",
        status=200,
        body=load_fixture("audiobook.json"),
    )
    response = await authenticated_client.get_audiobook("6SJQ8VzM5PlDy11wMtcD6v")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/audiobooks/6SJQ8VzM5PlDy11wMtcD6v",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )


async def test_get_audiobook_chapters(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving audiobook chapters."""
    responses.get(
        f"{SPOTIFY_URL}/v1/audiobooks/6SJQ8VzM5PlDy11wMtcD6v/chapters?limit=50",
        status=200,
        body=load_fixture("audiobook_chapters.json"),
    )
    response = await authenticated_client.get_audiobook_chapters(
        "6SJQ8VzM5PlDy11wMtcD6v"
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/audiobooks/6SJQ8VzM5PlDy11wMtcD6v/chapters",
        METH_GET,
        headers=HEADERS,
        params={"limit": 50},
        json=None,
    )


async def test_get_saved_audiobooks(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving saved audiobooks."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/audiobooks?limit=48",
        status=200,
        body=load_fixture("saved_audiobooks.json"),
    )
    response = await authenticated_client.get_saved_audiobooks()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/audiobooks",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_show_episodes(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving episodes of a show."""
    responses.get(
        f"{SPOTIFY_URL}/v1/shows/0e30iIgSffe6xJhFKe35Db/episodes?limit=48",
        status=200,
        body=load_fixture("show_episodes.json"),
    )
    response = await authenticated_client.get_show_episodes("0e30iIgSffe6xJhFKe35Db")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/shows/0e30iIgSffe6xJhFKe35Db/episodes",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_chapter(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving chapter."""
    responses.get(
        f"{SPOTIFY_URL}/v1/chapters/0bnJ1qcNgHwwPWbDJAia57",
        status=200,
        body=load_fixture("chapter.json"),
    )
    response = await authenticated_client.get_chapter("0bnJ1qcNgHwwPWbDJAia57")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/chapters/0bnJ1qcNgHwwPWbDJAia57",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )


async def test_get_saved_episodes(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving saved episodes."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/episodes?limit=48",
        status=200,
        body=load_fixture("saved_episodes.json"),
    )
    response = await authenticated_client.get_saved_episodes()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/episodes",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": "New Name"},
        {"description": "New Description"},
        {"public": False},
        {"collaborative": True},
        {
            "name": "New Name",
            "description": "New Description",
            "public": False,
            "collaborative": True,
        },
    ],
)
async def test_update_playlist_details(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    kwargs: dict[str, Any],
) -> None:
    """Test updating a playlist."""
    responses.put(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        status=200,
        body="",
    )
    await authenticated_client.update_playlist_details(
        "37i9dQZF1DXcBWIGoYBM5M", **kwargs
    )
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        METH_PUT,
        headers=HEADERS,
        params=None,
        json=kwargs,
    )


async def test_get_playlist_items(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playlist items."""
    responses.get(
        f"{SPOTIFY_URL}/v1/playlists/1Cp6VQCKf2VL4sP09jN9oX/items?limit=48",
        status=200,
        body=load_fixture("playlist_items.json"),
    )
    response = await authenticated_client.get_playlist_items("1Cp6VQCKf2VL4sP09jN9oX")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/1Cp6VQCKf2VL4sP09jN9oX/items",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"]},
        {
            "uris": [
                "spotify:track:4iV5W9uYEdYUVa79Axb7Rh",
                "spotify:track:1301WleyT98MSxVHPZCA6M",
            ]
        },
        {"uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"], "range_start": 5},
        {"uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"], "range_length": 10},
        {
            "uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"],
            "range_start": 5,
            "range_length": 10,
        },
        {"uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"], "insert_before": 10},
        {
            "uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"],
            "snapshot_id": "AAAACG9jmE4O/USJ4XSA7mfhfXkaxawY",
        },
    ],
)
async def test_update_playlist_items(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    kwargs: dict[str, Any],
) -> None:
    """Test updating playlist items."""
    responses.put(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M/items",
        status=200,
        body=load_fixture("playlist_update_items.json"),
    )
    assert (
        await authenticated_client.update_playlist_items(
            "37i9dQZF1DXcBWIGoYBM5M", **kwargs
        )
        == "AAAACG9jmE4O/USJ4XSA7mfhfXkaxawY"
    )
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M/items",
        METH_PUT,
        headers=HEADERS,
        params=None,
        json=kwargs,
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"]},
        {
            "uris": [
                "spotify:track:4iV5W9uYEdYUVa79Axb7Rh",
                "spotify:track:1301WleyT98MSxVHPZCA6M",
            ],
            "position": 5,
        },
    ],
)
async def test_add_playlist_items(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    kwargs: dict[str, Any],
) -> None:
    """Test adding playlist items."""
    responses.post(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M/items",
        status=201,
        body=load_fixture("playlist_update_items.json"),
    )
    assert (
        await authenticated_client.add_playlist_items(
            "37i9dQZF1DXcBWIGoYBM5M", **kwargs
        )
        == "AAAACG9jmE4O/USJ4XSA7mfhfXkaxawY"
    )
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M/items",
        METH_POST,
        headers=HEADERS,
        params=None,
        json=kwargs,
    )


async def test_add_too_many_playlist_items(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test adding too many playlist items."""
    with pytest.raises(ValueError, match="Maximum of 100 tracks can be added at once"):
        await authenticated_client.add_playlist_items(
            "37i9dQZF1DXcBWIGoYBM5M", uris=["abc"] * 101
        )
    responses.assert_not_called()  # type: ignore[no-untyped-call]


@pytest.mark.parametrize(
    ("kwargs", "expected_json"),
    [
        (
            {"uris": ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"]},
            {"tracks": [{"uri": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh"}]},
        ),
        (
            {
                "uris": [
                    "spotify:track:4iV5W9uYEdYUVa79Axb7Rh",
                    "spotify:track:1301WleyT98MSxVHPZCA6M",
                ],
                "snapshot_id": "AAAACG9jmE4O/USJ4XSA7mfhfXkaxawY",
            },
            {
                "tracks": [
                    {"uri": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh"},
                    {"uri": "spotify:track:1301WleyT98MSxVHPZCA6M"},
                ],
                "snapshot_id": "AAAACG9jmE4O/USJ4XSA7mfhfXkaxawY",
            },
        ),
    ],
)
async def test_remove_playlist_items(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    kwargs: dict[str, Any],
    expected_json: dict[str, Any],
) -> None:
    """Test removing playlist items."""
    responses.delete(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M/items",
        status=200,
        body=load_fixture("playlist_update_items.json"),
    )
    assert (
        await authenticated_client.remove_playlist_items(
            "37i9dQZF1DXcBWIGoYBM5M", **kwargs
        )
        == "AAAACG9jmE4O/USJ4XSA7mfhfXkaxawY"
    )
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M/items",
        METH_DELETE,
        headers=HEADERS,
        params=None,
        json=expected_json,
    )


async def test_remove_too_many_playlist_items(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test removing too many playlist items."""
    with pytest.raises(
        ValueError, match="Maximum of 100 tracks can be removed at once"
    ):
        await authenticated_client.remove_playlist_items(
            "37i9dQZF1DXcBWIGoYBM5M", uris=["abc"] * 101
        )
    responses.assert_not_called()  # type: ignore[no-untyped-call]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"description": "New Playlist"},
        {"public": False},
        {"collaborative": True},
        {"public": False, "collaborative": True},
    ],
)
async def test_create_playlist(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    snapshot: SnapshotAssertion,
    kwargs: dict[str, Any],
) -> None:
    """Test creating a playlist."""
    responses.post(
        f"{SPOTIFY_URL}/v1/me/playlists",
        status=201,
        body=load_fixture("new_playlist.json"),
    )
    assert (
        await authenticated_client.create_playlist("My Playlist", **kwargs) == snapshot
    )
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/playlists",
        METH_POST,
        headers=HEADERS,
        params=None,
        json={"name": "My Playlist"} | kwargs,
    )


async def test_get_playlist_cover_image(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playlist cover image."""
    responses.get(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M/images",
        status=200,
        body=load_fixture("playlist_cover_image.json"),
    )
    response = await authenticated_client.get_playlist_cover_image(
        "37i9dQZF1DXcBWIGoYBM5M"
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M/images",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )


async def test_search(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test searching for tracks."""
    responses.get(
        f"{SPOTIFY_URL}/v1/search?limit=5&q=Never+Gonna+Give+You+Up&type=track",
        status=200,
        body=load_fixture("search.json"),
    )
    response = await authenticated_client.search(
        "Never Gonna Give You Up", [SearchType.TRACK]
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/search",
        METH_GET,
        headers=HEADERS,
        params={"q": "Never Gonna Give You Up", "type": "track", "limit": 5},
        json=None,
    )


async def test_save_to_library(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test saving items to library."""
    responses.put(
        f"{SPOTIFY_URL}/v1/me/library?uris=spotify%3Atrack%3A4iV5W9uYEdYUVa79Axb7Rh%2Cspotify%3Aalbum%3A1uyf3l2d4XYwiEqAb7t7fX",
        status=200,
        body="",
    )
    await authenticated_client.save_to_library(
        ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh", "spotify:album:1uyf3l2d4XYwiEqAb7t7fX"]
    )
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/library",
        METH_PUT,
        headers=HEADERS,
        params={
            "uris": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh,"
            "spotify:album:1uyf3l2d4XYwiEqAb7t7fX"
        },
        json=None,
    )


async def test_save_to_library_no_uris(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test saving empty list to library does nothing."""
    await authenticated_client.save_to_library([])
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_save_to_library_too_many(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test saving too many items to library raises ValueError."""
    with pytest.raises(ValueError, match="Maximum of 40 URIs can be saved at once"):
        await authenticated_client.save_to_library(["spotify:track:abc"] * 41)
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_remove_from_library(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test removing items from library."""
    responses.delete(
        f"{SPOTIFY_URL}/v1/me/library?uris=spotify%3Atrack%3A4iV5W9uYEdYUVa79Axb7Rh%2Cspotify%3Aalbum%3A1uyf3l2d4XYwiEqAb7t7fX",
        status=200,
        body="",
    )
    await authenticated_client.remove_from_library(
        ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh", "spotify:album:1uyf3l2d4XYwiEqAb7t7fX"]
    )
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/library",
        METH_DELETE,
        headers=HEADERS,
        params={
            "uris": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh,"
            "spotify:album:1uyf3l2d4XYwiEqAb7t7fX"
        },
        json=None,
    )


async def test_remove_from_library_no_uris(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test removing empty list from library does nothing."""
    await authenticated_client.remove_from_library([])
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_remove_from_library_too_many(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test removing too many items from library raises ValueError."""
    with pytest.raises(ValueError, match="Maximum of 40 URIs can be removed at once"):
        await authenticated_client.remove_from_library(["spotify:track:abc"] * 41)
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_are_in_library(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test checking if items are in library."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/library/contains?uris=spotify%3Atrack%3A4iV5W9uYEdYUVa79Axb7Rh%2Cspotify%3Aalbum%3A1uyf3l2d4XYwiEqAb7t7fX",
        status=200,
        body=load_fixture("library_contains.json"),
    )
    response = await authenticated_client.are_in_library(
        ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh", "spotify:album:1uyf3l2d4XYwiEqAb7t7fX"]
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/library/contains",
        METH_GET,
        headers=HEADERS,
        params={
            "uris": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh,"
            "spotify:album:1uyf3l2d4XYwiEqAb7t7fX"
        },
        json=None,
    )


async def test_are_in_library_no_uris(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test checking empty list returns empty dict."""
    response = await authenticated_client.are_in_library([])
    assert response == {}
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_are_in_library_too_many(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test checking too many items raises ValueError."""
    with pytest.raises(ValueError, match="Maximum of 40 URIs can be checked at once"):
        await authenticated_client.are_in_library(["spotify:track:abc"] * 41)
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_is_added_to_library(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test checking single item in library."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/library/contains?uris=spotify%3Atrack%3A4iV5W9uYEdYUVa79Axb7Rh",
        status=200,
        body=load_fixture("library_contains.json"),
    )
    result = await authenticated_client.is_added_to_library(
        "spotify:track:4iV5W9uYEdYUVa79Axb7Rh"
    )
    assert result is False


async def test_get_audio_features(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving audio features."""
    responses.get(
        f"{SPOTIFY_URL}/v1/audio-features/11dFghVXANMlKmJXsNCbNl",
        status=200,
        body=load_fixture("audio_features.json"),
    )
    response = await authenticated_client.get_audio_features("11dFghVXANMlKmJXsNCbNl")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/audio-features/11dFghVXANMlKmJXsNCbNl",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )
