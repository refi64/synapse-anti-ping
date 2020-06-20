# pyright: reportUnknownMemberType=false
from typing import *
from typing import cast

from datetime import datetime, timedelta, timezone
from twisted.internet import task  # type: ignore

if TYPE_CHECKING:
    from .spam_checker_api import SpamCheckerApi

import collections
import logging

from .config import Config, OffenceConfig
from .matrix import Matrix, Mjolnir
from .mentions import get_mention_count
from .offender import Offender, OffenderState, Offence, OffenceList, OffenceListClassifier
from .utils import *

logger = logging.getLogger('synapse_anti_ping.antispam')


class AntiSpam:
    def __init__(self, config: Config, api: 'SpamCheckerApi'):
        self.api = api
        self.config = config

        if self.config.user.homeserver is None:
            self.config.user.homeserver = self.api.hs.config.public_baseurl

        self.matrix = Matrix(self.config)
        self.matrix.start()

        self.mjolnir = Mjolnir(self.config, self.matrix)

        self.offenders: DefaultDict[str, Offender] = collections.defaultdict(
            lambda: Offender(OffenceList(cap=config.offences.history_size)))

        self.gc_task = task.LoopingCall(self._gc_callback)
        self.gc_task.start(self.config.offences.gc_interval_minutes * 60)

        self.include_rooms = compile_pattern_alternatives(config.rooms.include)
        self.exclude_rooms = compile_pattern_alternatives(config.rooms.exclude)
        self.exclude_members = compile_pattern_alternatives(config.members.exclude)

    def _gc_callback(self) -> None:
        to_remove: Set[str] = set()

        for offender, data in self.offenders.items():
            data.offences.clear_expired()
            if data.offences:
                if self._classify_offences(data.offences) == OffenceListClassifier.OKAY:
                    data.state = OffenderState.OKAY
            else:
                to_remove.add(offender)

        for offender in to_remove:
            del self.offenders[offender]

    @property
    def full_user(self) -> str:
        return f'@{self.config.user.user}:{self.api.hs.config.server_name}'

    @staticmethod
    def parse_config(data: Dict[str, Any]) -> Config:
        return Config.from_data(data)

    def _make_offence(self, origin: datetime, config: OffenceConfig) -> Offence:
        return Offence(weight=config.weight,
                       expiration=origin + timedelta(minutes=config.expires_minutes))

    def _classify_offences(self, offences: OffenceList) -> OffenceListClassifier:
        return offences.classify(spam_limit=self.config.offences.limits.spam,
                                 ban_limit=self.config.offences.limits.ban)

    def check_event_for_spam(self, event: Dict[str, Any]) -> bool:
        event_type = optional_safe_cast(str, event.get('type'))
        if event_type != 'm.room.message':
            return False

        room_id = safe_cast(str, event['room_id'])
        if (not room_id.endswith(f':{self.api.hs.config.server_name}')
                or self.include_rooms.match(room_id) is None
                or self.exclude_rooms.match(room_id) is not None or room_id == self.config.log.room
                or room_id == self.config.mjolnir.room):
            return False

        sender = safe_cast(str, event['sender'])
        if (self.exclude_members.match(sender) is not None or sender == self.full_user):
            return False

        ms = safe_cast(int, event['origin_server_ts'])
        timestamp = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

        offence: Optional[Offence] = None
        content_type = safe_cast(str, event['content']['msgtype'])

        if content_type == 'm.text':
            formatted_body = optional_safe_cast(str, event['content'].get('formatted_body'))

            if formatted_body is not None:
                if self.config.offences.mentions.enabled or self.config.offences.mass_mentions.enabled:
                    mentions = get_mention_count(
                        formatted_body,
                        limit=self.config.offences.mass_mentions.upgrade_at
                        if self.config.offences.mass_mentions.enabled else 1)
                    if (self.config.offences.mass_mentions.enabled
                            and mentions == self.config.offences.mass_mentions.upgrade_at):
                        offence = self._make_offence(timestamp, self.config.offences.mass_mentions)
                    elif self.config.offences.mentions.enabled and mentions:
                        offence = self._make_offence(timestamp, self.config.offences.mentions)

        if offence is None:
            if content_type in ('m.image', 'm.audio', 'm.video'):
                offence_config = self.config.offences.media_spam
            else:
                offence_config = self.config.offences.text_spam

            if offence_config.enabled:
                offence = self._make_offence(timestamp, offence_config)

        if offence is not None:
            data = self.offenders[sender]
            data.offences.push(offence)
            data.offences.clear_expired()

            classifier = self._classify_offences(data.offences)
            if classifier == OffenceListClassifier.BAN:
                if data.state < OffenderState.BANNED:
                    logger.info(f'Ban on {sender} room {room_id}')
                    self.matrix.send_message(f'{sender} was banned for spam in {room_id}',
                                             room=self.config.log.room,
                                             notice=True)
                    self.mjolnir.ban(sender)
                    data.state = OffenderState.BANNED
                return True
            elif classifier == OffenceListClassifier.SPAM:
                if data.state < OffenderState.ALERTED:
                    logger.info(f'Spam on {sender} from {room_id}')
                    self.matrix.send_message(f'{sender} was submitting spam in {room_id}',
                                             room=self.config.log.room,
                                             notice=True)

                    alert = f'{sender} {self.config.offences.spam_alert}'
                    formatted = (f'<a href="https://matrix.to/#/{sender}">{sender}</a>'
                                 f' {self.config.offences.spam_alert}')
                    self.matrix.send_message(alert, room=room_id, formatted=formatted)
                    data.state = OffenderState.ALERTED
                return True
            else:
                data.state = OffenderState.OKAY

        return False

    def user_may_invite(self, inviter_user_id: str, invitee_user_id: str, room_id: str) -> bool:
        return True

    def check_username_for_spam(self, user_profile: Dict[str, Any]) -> bool:
        return True

    def user_may_create_room(self, user_id: str) -> bool:
        return True

    def user_may_create_room_alias(self, user_id: str, room_alias: str) -> bool:
        return True

    def user_may_publish_room(self, user_id: str, room_id: str) -> bool:
        return True
