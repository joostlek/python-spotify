"""Asynchronous Python client for Spotify."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aiohttp
from aiohttp.hdrs import METH_DELETE, METH_GET, METH_POST, METH_PUT
from aioresponses import CallbackResult, aioresponses
import pytest
from yarl import URL

from spotifyaio import RepeatMode, SpotifyClient, SpotifyConnectionError

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


async def test_get_albums(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving albums."""
    responses.get(
        f"{SPOTIFY_URL}/v1/albums?ids=3IqzqH6ShrRtie9Yd2ODyG%252C1A2GTWGtFfWp7KSQTwWOyo%252C2noRn2Aes5aoNVsU6iWTh",
        status=200,
        body=load_fixture("albums.json"),
    )
    response = await authenticated_client.get_albums(
        [
            "spotify:album:3IqzqH6ShrRtie9Yd2ODyG",
            "1A2GTWGtFfWp7KSQTwWOyo",
            "2noRn2Aes5aoNVsU6iWTh",
        ]
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/albums",
        METH_GET,
        headers=HEADERS,
        params={
            "ids": "3IqzqH6ShrRtie9Yd2ODyG,1A2GTWGtFfWp7KSQTwWOyo,2noRn2Aes5aoNVsU6iWTh"
        },
        json=None,
    )


async def test_get_no_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving no albums."""
    response = await authenticated_client.get_albums([])
    assert response == []
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_get_too_many_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving too many albums."""
    with pytest.raises(
        ValueError, match="Maximum of 20 albums can be requested at once"
    ):
        await authenticated_client.get_albums(["abc"] * 21)
    responses.assert_not_called()  # type: ignore[no-untyped-call]


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


async def test_save_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test saving albums."""
    responses.put(
        f"{SPOTIFY_URL}/v1/me/albums?ids=3IqzqH6ShrRtie9Yd2ODyG%252C1A2GTWGtFfWp7KSQTwWOyo%252C2noRn2Aes5aoNVsU6iWTh",
        status=200,
    )
    await authenticated_client.save_albums(
        [
            "spotify:album:3IqzqH6ShrRtie9Yd2ODyG",
            "1A2GTWGtFfWp7KSQTwWOyo",
            "2noRn2Aes5aoNVsU6iWTh",
        ]
    )
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/albums",
        METH_PUT,
        headers=HEADERS,
        params={
            "ids": "3IqzqH6ShrRtie9Yd2ODyG,1A2GTWGtFfWp7KSQTwWOyo,2noRn2Aes5aoNVsU6iWTh"
        },
        json=None,
    )


async def test_save_no_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test saving no albums."""
    await authenticated_client.save_albums([])
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_save_too_many_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test saving too many albums."""
    with pytest.raises(ValueError, match="Maximum of 50 albums can be saved at once"):
        await authenticated_client.save_albums(["abc"] * 51)
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_removing_saved_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test deleting saved albums."""
    responses.delete(
        f"{SPOTIFY_URL}/v1/me/albums?ids=3IqzqH6ShrRtie9Yd2ODyG%252C1A2GTWGtFfWp7KSQTwWOyo%252C2noRn2Aes5aoNVsU6iWTh",
        status=200,
    )
    await authenticated_client.remove_saved_albums(
        [
            "spotify:album:3IqzqH6ShrRtie9Yd2ODyG",
            "1A2GTWGtFfWp7KSQTwWOyo",
            "2noRn2Aes5aoNVsU6iWTh",
        ]
    )
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/albums",
        METH_DELETE,
        headers=HEADERS,
        params={
            "ids": "3IqzqH6ShrRtie9Yd2ODyG,1A2GTWGtFfWp7KSQTwWOyo,2noRn2Aes5aoNVsU6iWTh"
        },
        json=None,
    )


async def test_removing_no_saved_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test removing no saved albums."""
    await authenticated_client.remove_saved_albums([])
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_removing_too_many_saved_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test removing too many saved albums."""
    with pytest.raises(ValueError, match="Maximum of 50 albums can be removed at once"):
        await authenticated_client.remove_saved_albums(["abc"] * 51)
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_checking_saved_albums(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test checking saved albums."""
    responses.get(
        f"{SPOTIFY_URL}/v1/me/albums/contains?ids=3IqzqH6ShrRtie9Yd2ODyG%252C1A2GTWGtFfWp7KSQTwWOyo%252C2noRn2Aes5aoNVsU6iWTh",
        status=200,
        body=load_fixture("album_saved.json"),
    )
    response = await authenticated_client.are_albums_saved(
        [
            "spotify:album:3IqzqH6ShrRtie9Yd2ODyG",
            "1A2GTWGtFfWp7KSQTwWOyo",
            "2noRn2Aes5aoNVsU6iWTh",
        ]
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/me/albums/contains",
        METH_GET,
        headers=HEADERS,
        params={
            "ids": "3IqzqH6ShrRtie9Yd2ODyG,1A2GTWGtFfWp7KSQTwWOyo,2noRn2Aes5aoNVsU6iWTh"
        },
        json=None,
    )


async def test_checking_no_saved_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test checking no saved albums."""
    await authenticated_client.are_albums_saved([])
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_checking_too_many_saved_albums(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
) -> None:
    """Test checking too many saved albums."""
    with pytest.raises(ValueError, match="Maximum of 20 albums can be checked at once"):
        await authenticated_client.are_albums_saved(["abc"] * 21)
    responses.assert_not_called()  # type: ignore[no-untyped-call]


async def test_get_audiobooks(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving audiobooks."""
    responses.get(
        f"{SPOTIFY_URL}/v1/audiobooks?ids=3o0RYoo5iOMKSmEbunsbvW%252C1A2GTWGtFfWp7KSQTwWOyo%252C2noRn2Aes5aoNVsU6iWTh",
        status=200,
        body=load_fixture("audiobooks.json"),
    )
    response = await authenticated_client.get_audiobooks(
        [
            "spotify:episode:3o0RYoo5iOMKSmEbunsbvW",
            "1A2GTWGtFfWp7KSQTwWOyo",
            "2noRn2Aes5aoNVsU6iWTh",
        ]
    )
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/audiobooks",
        METH_GET,
        headers=HEADERS,
        params={
            "ids": "3o0RYoo5iOMKSmEbunsbvW,1A2GTWGtFfWp7KSQTwWOyo,2noRn2Aes5aoNVsU6iWTh"
        },
        json=None,
    )


@pytest.mark.parametrize(
    "playback_fixture",
    [
        "playback_1.json",
        "playback_2.json",
        "playback_3.json",
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


async def test_get_playlist(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playlist."""
    responses.get(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        status=200,
        body=load_fixture("playlist.json"),
    )
    response = await authenticated_client.get_playlist("37i9dQZF1DXcBWIGoYBM5M")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )


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
        "37i9dQZF1DXcBWIGoYBM5M",
        "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
        "spotify:user:chilledcow:playlist:37i9dQZF1DXcBWIGoYBM5M",
    ],
)
async def test_get_playlist_variation(
    responses: aioresponses,
    authenticated_client: SpotifyClient,
    playlist_id: str,
) -> None:
    """Test retrieving playlist with different inputs."""
    responses.get(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        status=200,
        body=load_fixture("playlist.json"),
    )
    await authenticated_client.get_playlist(playlist_id)
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/playlists/37i9dQZF1DXcBWIGoYBM5M",
        METH_GET,
        headers=HEADERS,
        params=None,
        json=None,
    )


async def test_get_featured_playlists(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/browse/featured-playlists?limit=48",
        status=200,
        body=load_fixture("featured_playlists.json"),
    )
    response = await authenticated_client.get_featured_playlists()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/browse/featured-playlists",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_category_playlists(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving playback state."""
    responses.get(
        f"{SPOTIFY_URL}/v1/browse/categories/rock/playlists?limit=48",
        status=200,
        body=load_fixture("category_playlists.json"),
    )
    response = await authenticated_client.get_category_playlists("rock")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/browse/categories/rock/playlists",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
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


async def test_get_user(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving user."""
    responses.get(
        f"{SPOTIFY_URL}/v1/users/smedjan",
        status=200,
        body=load_fixture("user.json"),
    )
    response = await authenticated_client.get_user("smedjan")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/users/smedjan",
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


async def test_get_new_releases(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving new releases."""
    responses.get(
        f"{SPOTIFY_URL}/v1/browse/new-releases?limit=48",
        status=200,
        body=load_fixture("new_releases.json"),
    )
    response = await authenticated_client.get_new_releases()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/browse/new-releases",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


async def test_get_category(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving a category."""
    responses.get(
        f"{SPOTIFY_URL}/v1/browse/categories/dinner",
        status=200,
        body=load_fixture("category.json"),
    )
    response = await authenticated_client.get_category("dinner")
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/browse/categories/dinner",
        METH_GET,
        headers=HEADERS,
        params=None,
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


async def test_get_categories(
    responses: aioresponses,
    snapshot: SnapshotAssertion,
    authenticated_client: SpotifyClient,
) -> None:
    """Test retrieving categories."""
    responses.get(
        f"{SPOTIFY_URL}/v1/browse/categories?limit=48",
        status=200,
        body=load_fixture("categories.json"),
    )
    response = await authenticated_client.get_categories()
    assert response == snapshot
    responses.assert_called_once_with(
        f"{SPOTIFY_URL}/v1/browse/categories",
        METH_GET,
        headers=HEADERS,
        params={"limit": 48},
        json=None,
    )


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
