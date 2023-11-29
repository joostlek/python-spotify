from dataclasses import dataclass

from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class Device(DataClassORJSONMixin):

    id: str
    is_active: bool
    is_private_session: bool
    name: str
    supports_volume: bool
    type: str
    volume_percent: int


@dataclass
class PlaybackState(DataClassORJSONMixin):

    device: Device
