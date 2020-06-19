import os, sys
sys.path.append(os.path.dirname(__file__) + '/..')

from synapse_anti_ping.mentions import get_mention_count


def test_mentions():
    assert get_mention_count('', limit=1) == 0
    assert get_mention_count('<a href>', limit=1) == 0
    assert get_mention_count('<a href="https://matrix.to/#/@user:instance.chat">', limit=1) == 1
    assert get_mention_count('<a href="https://matrix.to/#/@user:instance.chat">', limit=0) == 0
