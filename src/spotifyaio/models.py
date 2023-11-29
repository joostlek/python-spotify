"""Models for Spotify."""
from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class Device(DataClassORJSONMixin):
    """Device model."""

    device_id: str = field(metadata=field_options(alias="id"))
    is_active: bool
    is_private_session: bool
    name: str
    supports_volume: bool
    device_type: str = field(metadata=field_options(alias="type"))
    volume_percent: int


@dataclass
class PlaybackState(DataClassORJSONMixin):
    """Playback state model."""

    device: Device
