from typing import *

from html.parser import HTMLParser
from urllib.parse import urlparse


class _MentionCountingParser(HTMLParser):
    class LimitReached(Exception):
        def __init__(self, count: int) -> None:
            self.count = count

    def __init__(self, limit: int) -> None:
        super().__init__()
        self.count = 0
        self.limit = limit

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag != 'a':
            return

        for attr, value in attrs:
            if attr == 'href' and value is not None:
                try:
                    url = urlparse(value)
                except ValueError:
                    continue

                if url.netloc == 'matrix.to' and url.fragment.startswith('/@'):
                    self.count += 1
                    if self.count >= self.limit:
                        raise _MentionCountingParser.LimitReached(self.count)
                    break


def get_mention_count(body: str, *, limit: int) -> int:
    parser = _MentionCountingParser(limit)

    try:
        parser.feed(body)
    except _MentionCountingParser.LimitReached:
        return limit
    else:
        return parser.count
