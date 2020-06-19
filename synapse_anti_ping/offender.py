from typing import *

from dataclasses import dataclass
from datetime import datetime, timezone
import enum
import functools

from .round_robin_heap import RoundRobinHeap


@functools.total_ordering
@dataclass(order=False)
class Offence:
    expiration: datetime
    weight: int

    @property
    def expired(self) -> bool:
        return datetime.now(tz=timezone.utc) > self.expiration

    def __lt__(self, other: 'Offence') -> bool:
        return self.expiration < other.expiration


class OffenceListClassifier(enum.Enum):
    OKAY = 0
    SPAM = 1
    BAN = 2


class OffenceList:
    def __init__(self, cap: int) -> None:
        self._heap: RoundRobinHeap[Offence] = RoundRobinHeap(cap=cap)

    @property
    def total_weight(self) -> int:
        return sum(offence.weight for offence in self._heap)

    @property
    def oldest(self) -> Offence:
        return self._heap.top

    def push(self, offence: Offence) -> None:
        self._heap.push(offence)

    def pop(self) -> Offence:
        return self._heap.pop()

    def clear_expired(self) -> None:
        while self and self.oldest.expired:
            self.pop()

    def classify(self, *, spam_limit: int, ban_limit: int) -> OffenceListClassifier:
        assert spam_limit <= ban_limit

        weight = self.total_weight
        if weight >= ban_limit:
            return OffenceListClassifier.BAN
        elif weight >= spam_limit:
            return OffenceListClassifier.SPAM
        else:
            return OffenceListClassifier.OKAY

    def __bool__(self) -> bool:
        return bool(self._heap)

    def __len__(self) -> int:
        return len(self._heap)

    def __iter__(self) -> Iterator[Offence]:
        yield from iter(self._heap)


@functools.total_ordering
class OffenderState(enum.Enum):
    OKAY = 0
    ALERTED = 1
    BANNED = 2

    def __lt__(self, other: 'OffenderState') -> bool:
        return cast(int, self.value) < cast(int, other.value)


@dataclass
class Offender:
    offences: OffenceList
    state: OffenderState = OffenderState.OKAY
