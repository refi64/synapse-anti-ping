from typing import *

# XXX: Can't use the C heapq module because it only takes vanilla lists
import importlib, sys, types

sys.modules['_heapq'] = types.ModuleType('_heapq')

import heapq
importlib.reload(heapq)

from .round_robin_list import RoundRobinList

_T = TypeVar('_T')


class RoundRobinHeap(Generic[_T]):
    def __init__(self, *, cap: int) -> None:
        self._storage: RoundRobinList[_T] = RoundRobinList(cap=cap)

    @property
    def _storage_as_list(self) -> List[_T]:
        return cast(List[_T], self._storage)

    def push(self, item: _T) -> None:
        heapq.heappush(self._storage_as_list, item)

    def pop(self) -> _T:
        return heapq.heappop(self._storage_as_list)

    @property
    def top(self) -> _T:
        return self._storage_as_list[0]

    @property
    def full(self) -> bool:
        return self._storage.full

    @property
    def cap(self) -> int:
        return self._storage.cap

    def __len__(self) -> int:
        return len(self._storage_as_list)

    def __iter__(self) -> Iterator[_T]:
        yield from iter(self._storage)

    def __bool__(self) -> bool:
        return bool(self._storage)
