"""Asynchronous Python client for Spotify."""
import aiohttp
import pytest

from spotifyaio import SpotifyClient
from syrupy import SnapshotAssertion

from .syrupy import SpotifySnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Spotify extension."""
    return snapshot.use_extension(SpotifySnapshotExtension)


@pytest.fixture(name="spotify_client")
async def client() -> SpotifyClient:
    """Return a Spotify client."""
    async with aiohttp.ClientSession() as session, SpotifyClient(
        session=session,
    ) as spotify_client:
        yield spotify_client


@pytest.fixture(name="authenticated_client")
async def authenticated_client(
    spotify_client: SpotifyClient,
) -> SpotifyClient:
    """Return an authenticated Spotify client."""
    spotify_client.authenticate("test")
    return spotify_client
