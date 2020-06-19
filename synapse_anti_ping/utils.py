from typing import *

import fnmatch
import re

_T = TypeVar('_T')
_U = TypeVar('_U')


def safe_cast(target: Type[_U], obj: _T) -> _U:
    if not isinstance(obj, target):
        raise TypeError(f'Object was of type {type(obj)} which cannot be cast to {target}')

    return cast(_U, obj)


def optional_safe_cast(target: Type[_U], obj: _T) -> Optional[_U]:
    if obj is None:
        return None

    return safe_cast(target, obj)


def compile_pattern_alternatives(patterns: List[str]) -> 'Pattern[str]':
    if not patterns:
        return re.compile('^$')

    return re.compile('|'.join(f'{fnmatch.translate(p).replace("?:s", "?:")}' for p in patterns))
