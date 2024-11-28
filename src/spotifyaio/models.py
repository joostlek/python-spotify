"""Models for Spotify."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime  # noqa: TC003
from enum import IntEnum, StrEnum
from typing import Annotated, Any

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import Discriminator


class DeviceType(StrEnum):
    """Device type."""

    AUDIO_DONGLE = "AudioDongle"
    AUDIO_VIDEO_RECEIVER = "AVR"
    AUTOMOBILE = "Automobile"
    CAST_AUDIO = "CastAudio"
    CAST_VIDEO = "CastVideo"
    COMPUTER = "Computer"
    GAME_CONSOLE = "GameConsole"
    SET_TOP_BOX = "STB"
    SMARTPHONE = "Smartphone"
    SMARTWATCH = "Smartwatch"
    SPEAKER = "Speaker"
    TABLET = "Tablet"
    TV = "TV"
    UNKNOWN = "Unknown"


@dataclass
class Device(DataClassORJSONMixin):
    """Device model."""

    device_id: str | None = field(metadata=field_options(alias="id"))
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
    EP = "ep"
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
class SimplifiedAlbum(DataClassORJSONMixin):
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

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        return {
            **d,
            "album_type": d["album_type"].lower(),
        }


@dataclass
class Album(SimplifiedAlbum):
    """Album model."""

    tracks: list[SimplifiedTrack]

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        tracks = d.get("tracks", {}).pop("items", [])
        return {**d, "tracks": tracks}


@dataclass
class SavedAlbum(DataClassORJSONMixin):
    """Saved album model."""

    added_at: datetime
    album: Album


@dataclass
class SavedAlbumResponse(DataClassORJSONMixin):
    """SavedAlbum response model."""

    items: list[SavedAlbum]

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        items = [item for item in d["items"] if item is not None]
        return {"items": items}


@dataclass
class NewReleasesResponse(DataClassORJSONMixin):
    """NewReleases response model."""

    albums: NewReleasesResponseInner


@dataclass
class NewReleasesResponseInner(DataClassORJSONMixin):
    """NewReleases response model."""

    items: list[SimplifiedAlbum]


@dataclass
class SavedShow(DataClassORJSONMixin):
    """Saved Show model."""

    added_at: datetime
    show: SimplifiedShow


@dataclass
class SavedShowResponse(DataClassORJSONMixin):
    """SavedShow response model."""

    items: list[SavedShow]


@dataclass
class SavedTrack(DataClassORJSONMixin):
    """Saved track model."""

    added_at: datetime
    track: Track


@dataclass
class SavedTrackResponse(DataClassORJSONMixin):
    """SavedTrack response model."""

    items: list[SavedTrack]


@dataclass
class PlayedTrackResponse(DataClassORJSONMixin):
    """PlayedTrack response model."""

    items: list[PlayedTrack]


@dataclass
class PlayedTrack(DataClassORJSONMixin):
    """Played track model."""

    played_at: datetime
    track: Track
    context: Context | None = None


@dataclass
class ArtistResponse(DataClassORJSONMixin):
    """Artist response model."""

    artists: ArtistResponseItem


@dataclass
class ArtistResponseItem(DataClassORJSONMixin):
    """Artist response model."""

    items: list[Artist]


@dataclass
class Artist(SimplifiedArtist):
    """Artist model."""

    images: list[Image]


@dataclass
class TopArtistsResponse(DataClassORJSONMixin):
    """Top artists response model."""

    items: list[Artist]


@dataclass
class TopTracksResponse(DataClassORJSONMixin):
    """Top tracks response model."""

    items: list[Track]


@dataclass
class SimplifiedTrack(DataClassORJSONMixin):
    """SimplifiedTrack model."""

    track_id: str = field(metadata=field_options(alias="id"))
    artists: list[SimplifiedArtist]
    disc_number: int
    duration_ms: int
    explicit: bool
    external_urls: dict[str, str]
    href: str
    name: str
    is_local: bool
    track_number: int
    uri: str


class ItemType(StrEnum):
    """Item type."""

    TRACK = "track"
    EPISODE = "episode"


@dataclass
class Item(DataClassORJSONMixin):
    """Item model."""

    type: ItemType
    uri: str
    explicit: bool
    duration_ms: int
    external_urls: dict[str, str]
    href: str
    name: str


@dataclass
class Track(SimplifiedTrack, Item):
    """Track model."""

    type = ItemType.TRACK
    album: SimplifiedAlbum


@dataclass
class CurrentPlaying(DataClassORJSONMixin):
    """Current playing model."""

    context: Context | None
    progress_ms: int | None
    is_playing: bool
    item: Annotated[Item, Discriminator(field="type", include_subtypes=True)] | None
    currently_playing_type: str | None

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        if (item := d.get("item")) is not None and item.get("is_local"):
            return {**d, "item": None}
        return d


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

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        if d.get("images") is None:
            d["images"] = []
        return d


@dataclass
class Playlist(BasePlaylist):
    """Playlist model."""

    tracks: PlaylistTracks


@dataclass
class PlaylistTracks(DataClassORJSONMixin):
    """PlaylistTracks model."""

    items: list[PlaylistTrack]

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        items = [item for item in d["items"] if not item["is_local"]]
        return {"items": items}


@dataclass
class PlaylistTrack(DataClassORJSONMixin):
    """PlaylistTrack model."""

    track: Annotated[Item, Discriminator(field="type", include_subtypes=True)]


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

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        items = [item for item in d["items"] if item is not None]
        return {**d, "items": items}


@dataclass
class FeaturedPlaylistResponse(DataClassORJSONMixin):
    """Featured playlist response model."""

    message: str
    playlists: PlaylistResponse


@dataclass
class CategoryPlaylistResponse(DataClassORJSONMixin):
    """Category playlist response model."""

    playlists: PlaylistResponse


@dataclass
class CategoriesResponse(DataClassORJSONMixin):
    """Categories response model."""

    categories: CategoriesResponseInner


@dataclass
class CategoriesResponseInner(DataClassORJSONMixin):
    """Categories response model."""

    items: list[Category]


@dataclass
class Category(DataClassORJSONMixin):
    """Category model."""

    category_id: str = field(metadata=field_options(alias="id"))
    name: str
    href: str
    icons: list[Image]


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

    product: ProductType
    email: str | None = None


@dataclass
class SimplifiedShow(DataClassORJSONMixin):
    """SimplifiedShow model."""

    show_id: str = field(metadata=field_options(alias="id"))
    name: str
    uri: str
    images: list[Image]
    external_urls: dict[str, str]
    href: str
    publisher: str
    description: str
    total_episodes: int | None


@dataclass
class SimplifiedEpisode(DataClassORJSONMixin):
    """SimplifiedEpisode model."""

    episode_id: str = field(metadata=field_options(alias="id"))
    name: str
    uri: str
    images: list[Image]
    external_urls: dict[str, str]
    href: str
    duration_ms: int
    explicit: bool
    release_date: str
    release_date_precision: ReleaseDatePrecision
    description: str


@dataclass
class ShowEpisodesResponse(DataClassORJSONMixin):
    """ShowEpisodes response model."""

    items: list[SimplifiedEpisode]


@dataclass
class Episode(SimplifiedEpisode, Item):
    """Episode model."""

    type = ItemType.EPISODE
    show: SimplifiedShow


@dataclass
class Show(SimplifiedShow):
    """Show model."""

    episodes: list[SimplifiedEpisode]

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        episodes = d.get("episodes", {}).pop("items", [])
        return {**d, "episodes": episodes}


@dataclass
class AlbumsResponse(DataClassORJSONMixin):
    """Albums response model."""

    albums: list[Album]


@dataclass
class AlbumTracksResponse(DataClassORJSONMixin):
    """Album tracks response model."""

    items: list[SimplifiedTrack]


class Key(IntEnum):
    """Key of a track."""

    C = 0
    C_SHARP_D_FLAT = 1
    D = 2
    D_SHARP_E_FLAT = 3
    E = 4
    F = 5
    F_SHARP_G_FLAT = 6
    G = 7
    G_SHARP_A_FLAT = 8
    A = 9
    A_SHARP_B_FLAT = 10
    B = 11


class Mode(IntEnum):
    """Mode of a track."""

    MINOR = 0
    MAJOR = 1


class TimeSignature(IntEnum):
    """Time signature of a track."""

    ONE_FOUR = 1
    THREE_FOUR = 3
    FOUR_FOUR = 4
    FIVE_FOUR = 5
    SIX_FOUR = 6
    SEVEN_FOUR = 7


@dataclass
class AudioFeatures(DataClassORJSONMixin):
    """Audio features model."""

    danceability: float
    energy: float
    key: Key | None
    loudness: float
    mode: Mode
    speechiness: float
    acousticness: float
    instrumentalness: float
    liveness: float
    valence: float
    tempo: float
    time_signature: TimeSignature


@dataclass
class Chapter(DataClassORJSONMixin):
    """Chapter model."""

    chapter_id: str = field(metadata=field_options(alias="id"))
    chapter_number: int
    duration_ms: int
    images: list[Image]
    languages: list[str]
    name: str
    explicit: bool
    type: str
    uri: str
    external_urls: dict[str, str]


@dataclass
class Author(DataClassORJSONMixin):
    """Author model."""

    name: str


@dataclass
class Narrator(DataClassORJSONMixin):
    """Narrator model."""

    name: str


@dataclass
class Audiobook(DataClassORJSONMixin):
    """Audiobook model."""

    authors: list[Author]
    chapters: list[Chapter]
    description: str
    edition: str
    external_urls: dict[str, str]
    explicit: bool
    html_description: str
    audiobook_id: str = field(metadata=field_options(alias="id"))
    images: list[Image]
    languages: list[str]
    name: str
    narrators: list[Narrator]
    publisher: str
    total_chapters: int
    type: str
    uri: str

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        return {**d, "chapters": d.get("chapters", {}).pop("items", [])}


@dataclass
class AudiobooksResponse(DataClassORJSONMixin):
    """Audiobooks response model."""

    audiobooks: list[Audiobook]

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre deserialize hook."""
        items = [item for item in d["audiobooks"] if item is not None]
        return {"audiobooks": items}
