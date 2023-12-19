"""Asynchronous Python client for Spotify."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiohttp.hdrs import METH_GET, METH_POST, METH_PUT
from aioresponses import aioresponses
import pytest
from yarl import URL

from spotifyaio import RepeatMode

from . import load_fixture
from .const import HEADERS, SPOTIFY_URL

if TYPE_CHECKING:
    from spotifyaio import SpotifyClient
    from syrupy import SnapshotAssertion


@pytest.mark.parametrize(
    "playback_id",
    [
        1,
        2,
        3,
    ],
)
async def test_get_playback_state(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    playback_id: int,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player",
        status=200,
        body=load_fixture(f"playback_{playback_id}.json"),
    )
    response = await authenticated_client.get_playback()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player",
        METH_GET,
        headers=HEADERS,
        params=None,
        data=None,
    )


async def test_get_no_playback_state(
    authenticated_client: SpotifyClient,
    responses: aioresponses,
) -> None:
    """Test retrieving no playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/player",
        status=204,
    )
    response = await authenticated_client.get_playback()
    assert response is None
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player",
        METH_GET,
        headers=HEADERS,
        data=None,
        params=None,
    )


async def test_transfer_playback(
    authenticated_client: SpotifyClient,
    responses: aioresponses,
) -> None:
    """Test transferring playback."""
    responses.put(
        f"{SPOTIFY_URL}/v1/me/player",
        status=204,
    )
    await authenticated_client.transfer_playback("test")
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player",
        METH_PUT,
        headers=HEADERS,
        data={"device_ids": ["test"]},
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
        data=None,
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
        data=None,
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
        data=None,
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
    responses.put(
        url,
        status=204,
    )
    await authenticated_client.start_playback(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/play",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        data=expected_data,
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
    responses.put(
        url,
        status=204,
    )
    await authenticated_client.pause_playback(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/pause",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        data=None,
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
    responses.post(
        url,
        status=204,
    )
    await authenticated_client.next_track(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/next",
        METH_POST,
        headers=HEADERS,
        params=expected_params,
        data=None,
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
    responses.post(
        url,
        status=204,
    )
    await authenticated_client.previous_track(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/previous",
        METH_POST,
        headers=HEADERS,
        params=expected_params,
        data=None,
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
    responses.put(
        url,
        status=204,
    )
    await authenticated_client.seek_track(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/seek",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        data=None,
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
    responses.put(
        url,
        status=204,
    )
    await authenticated_client.set_repeat(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/repeat",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        data=None,
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
    responses.put(
        url,
        status=204,
    )
    await authenticated_client.set_volume(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/volume",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        data=None,
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
    responses.put(
        url,
        status=204,
    )
    await authenticated_client.set_shuffle(**arguments)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/player/shuffle",
        METH_PUT,
        headers=HEADERS,
        params=expected_params,
        data=None,
    )
