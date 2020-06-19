from typing import *

_T = TypeVar('_T')


class RoundRobinList(Generic[_T]):
    def __init__(self, *, cap: int) -> None:
        self._cap = cap
        self._next = 0
        self._length = 0
        self._storage: List[_T] = []
        self._storage.extend(cast(Iterable[_T], (None for _ in range(cap))))

    def append(self, item: _T) -> None:
        self._storage[self._next] = item
        self._next = (self._next + 1) % self._cap
        if self._length < self._cap:
            self._length += 1

    def _out_of_range(self) -> None:
        raise IndexError('list index out of range')

    def _get_real_index(self, i: int) -> int:
        if i >= 0:
            if i >= self._length:
                self._out_of_range()

            return (self._next - self._length + i) % self._cap
        else:
            if abs(i) > self._length:
                self._out_of_range()

            return (self._next + i) % self._cap

    def _pop(self, *, front: bool) -> _T:
        if not self:
            raise IndexError('pop from empty list')

        index = self._get_real_index(0 if front else -1)

        item = self._storage[index]
        self._storage[index] = cast(_T, None)
        self._length -= 1

        if not front:
            self._next = (self._next - 1) % self._cap

        return item

    def pop(self) -> _T:
        return self._pop(front=False)

    def pop_front(self) -> _T:
        return self._pop(front=True)

    @property
    def full(self) -> bool:
        return self._length == self._cap

    @property
    def cap(self) -> int:
        return self._cap

    def __bool__(self) -> bool:
        return self._length > 0

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, i: int) -> _T:
        return self._storage[self._get_real_index(i)]

    def __setitem__(self, i: int, item: _T) -> None:
        self._storage[self._get_real_index(i)] = item

    def __hasitem__(self, item: _T) -> bool:
        return item in iter(self)

    def __iter__(self) -> Iterator[_T]:
        for i in range(self._length):
            yield self[i]
