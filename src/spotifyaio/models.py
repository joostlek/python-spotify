"""Models for Spotify."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


class DeviceType(StrEnum):
    """Device type."""

    COMPUTER = "Computer"
    SMARTPHONE = "Smartphone"
    SPEAKER = "Speaker"


@dataclass
class Device(DataClassORJSONMixin):
    """Device model."""

    device_id: str = field(metadata=field_options(alias="id"))
    is_active: bool
    is_private_session: bool
    is_restricted: bool
    name: str
    device_type: DeviceType = field(metadata=field_options(alias="type"))
    volume_percent: int
    supports_volume: bool = True


@dataclass
class Devices(DataClassORJSONMixin):
    """Devices model."""

    devices: list[Device]


class RepeatMode(StrEnum):
    """Repeat mode."""

    OFF = "off"
    TRACK = "track"
    CONTEXT = "context"


class ContextType(StrEnum):
    """Context type."""

    ALBUM = "album"
    ARTIST = "artist"
    PLAYLIST = "playlist"
    COLLECTION = "collection"
    SHOW = "show"


@dataclass
class Context(DataClassORJSONMixin):
    """Context model."""

    external_urls: dict[str, str]
    href: str
    context_type: ContextType = field(metadata=field_options(alias="type"))
    uri: str


class AlbumType(StrEnum):
    """Album type."""

    ALBUM = "album"
    SINGLE = "single"
    COMPILATION = "compilation"


@dataclass
class Image(DataClassORJSONMixin):
    """Image model."""

    height: int | None
    width: int | None
    url: str


class ReleaseDatePrecision(StrEnum):
    """Release date precision."""

    YEAR = "year"
    MONTH = "month"
    DAY = "day"


@dataclass
class SimplifiedArtist(DataClassORJSONMixin):
    """Simplified artist model."""

    artist_id: str = field(metadata=field_options(alias="id"))
    name: str
    uri: str


@dataclass
class Album(DataClassORJSONMixin):
    """Album model."""

    album_type: AlbumType
    total_tracks: int
    album_id: str = field(metadata=field_options(alias="id"))
    images: list[Image]
    name: str
    release_date: str
    release_date_precision: ReleaseDatePrecision
    uri: str
    artists: list[SimplifiedArtist]


@dataclass
class Artist(DataClassORJSONMixin):
    """Artist model."""

    artist_id: str = field(metadata=field_options(alias="id"))
    name: str
    uri: str


@dataclass
class Track(DataClassORJSONMixin):
    """Track model."""

    track_id: str = field(metadata=field_options(alias="id"))
    album: Album
    artists: list[Artist]
    disc_number: int
    duration_ms: int
    explicit: bool
    external_ids: dict[str, str]
    external_urls: dict[str, str]
    href: str
    is_local: bool
    track_number: int
    object_type: str = field(metadata=field_options(alias="type"))
    uri: str


@dataclass
class CurrentPlaying(DataClassORJSONMixin):
    """Current playing model."""

    context: Context | None
    progress_ms: int | None
    is_playing: bool
    item: Track | None
    currently_playing_type: str | None


@dataclass
class PlaybackState(CurrentPlaying):
    """Playback state model."""

    device: Device
    shuffle: bool = field(metadata=field_options(alias="shuffle_state"))
    repeat_mode: RepeatMode = field(metadata=field_options(alias="repeat_state"))


class PlaylistOwnerType(StrEnum):
    """Playlist owner type."""

    USER = "user"


@dataclass
class PlaylistOwner(DataClassORJSONMixin):
    """Playlist owner model."""

    display_name: str
    external_urls: dict[str, str]
    href: str
    owner_id: str = field(metadata=field_options(alias="id"))
    object_type: str = field(metadata=field_options(alias="type"))
    uri: str


@dataclass
class BasePlaylist(DataClassORJSONMixin):
    """Base playlist model."""

    collaborative: bool
    description: str | None
    external_urls: dict[str, str]
    playlist_id: str = field(metadata=field_options(alias="id"))
    images: list[Image]
    name: str
    owner: PlaylistOwner
    public: bool | None
    object_type: str = field(metadata=field_options(alias="type"))
    uri: str


@dataclass
class Playlist(BasePlaylist):
    """Playlist model."""


@dataclass
class PlaylistResponse(DataClassORJSONMixin):
    """Playlist response model."""

    href: str
    items: list[BasePlaylist]
    limit: int
    next_list: str | None = field(metadata=field_options(alias="next"))
    offset: int
    previous_list: str | None = field(metadata=field_options(alias="previous"))
    total: int


@dataclass
class FeaturedPlaylistResponse(DataClassORJSONMixin):
    """Featured playlist response model."""

    message: str
    playlists: PlaylistResponse


@dataclass
class CategoryPlaylistResponse(DataClassORJSONMixin):
    """Category playlist response model."""

    playlists: PlaylistResponse


class ProductType(StrEnum):
    """Product type."""

    PREMIUM = "premium"
    FREE = "free"


@dataclass
class BaseUserProfile(DataClassORJSONMixin):
    """Base user profile model."""

    display_name: str
    user_id: str = field(metadata=field_options(alias="id"))
    images: list[Image]
    object_type: str = field(metadata=field_options(alias="type"))
    uri: str


@dataclass
class UserProfile(BaseUserProfile):
    """User profile model."""

    email: str
    product: ProductType
