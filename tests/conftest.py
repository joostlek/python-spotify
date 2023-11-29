"""Asynchronous Python client for Spotify."""
import pytest

from syrupy import SnapshotAssertion

from .syrupy import SpotifySnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Spotify extension."""
    return snapshot.use_extension(SpotifySnapshotExtension)
