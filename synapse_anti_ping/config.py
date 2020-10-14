from typing import *

from dataclasses import dataclass

import dataclasses
import marshmallow.validate
import marshmallow_dataclass


@dataclass
class MjolnirConfig:
    room: str
    banlist: str
    prefix: str = '!mjolnir'


@dataclass
class LogConfig:
    room: str


@dataclass
class UserConfig:
    # Order is dumb to follow dataclass restraints
    password: str
    user: str = dataclasses.field(
        metadata={'validate': marshmallow.validate.Regexp(r'^[a-z0-9._=\-/]+$')})
    homeserver: Optional[str] = None


@dataclass
class BanConfig:
    redactions: int
    minutes: int


@dataclass
class OffenceConfig:
    enabled: bool
    weight: int
    expires_minutes: float


@dataclass
class MassMentionsConfig(OffenceConfig):
    upgrade_at: int = 4


@dataclass
class Limits:
    spam: int = 20
    ban: int = 30


@dataclass
class OffencesConfig:
    text_spam: OffenceConfig = OffenceConfig(enabled=True, weight=2, expires_minutes=0.4)
    media_spam: OffenceConfig = OffenceConfig(enabled=True, weight=4, expires_minutes=0.5)
    mentions: OffenceConfig = OffenceConfig(enabled=True, weight=4, expires_minutes=0.5)
    mass_mentions: MassMentionsConfig = MassMentionsConfig(enabled=True,
                                                           weight=10,
                                                           expires_minutes=1)
    spam_alert: str = 'Stop spamming.'
    limits: Limits = Limits()
    history_size: int = 20
    gc_interval_minutes: int = 5


@dataclass
class RoomsConfig:
    exclude: List[str] = dataclasses.field(default_factory=lambda: [])
    include: List[str] = dataclasses.field(default_factory=lambda: ['*'])


@dataclass
class MembersConfig:
    exclude: List[str] = dataclasses.field(default_factory=lambda: [])


@dataclass
class Config:
    mjolnir: MjolnirConfig
    log: LogConfig
    user: UserConfig

    rooms: RoomsConfig = RoomsConfig()
    members: MembersConfig = MembersConfig()

    offences: OffencesConfig = OffencesConfig()

    @staticmethod
    def from_data(data: Mapping[str, Any]) -> 'Config':
        ConfigSchema = marshmallow_dataclass.class_schema(Config)
        return ConfigSchema().load(data)  # type: ignore
