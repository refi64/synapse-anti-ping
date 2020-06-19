import os, sys
sys.path.append(os.path.dirname(__file__) + '/..')

from synapse_anti_ping.round_robin_list import RoundRobinList


def test_round_robin_list():
    l = RoundRobinList(cap=3)
    assert not l
    assert len(l) == 0
    assert list(l) == []

    l.append(123)
    assert l
    assert len(l) == 1
    assert list(l) == [123]

    l.append(456)
    assert l
    assert len(l) == 2
    assert list(l) == [123, 456]

    assert l.pop() == 456
    assert l
    assert len(l) == 1
    assert list(l) == [123]

    assert l.pop() == 123
    assert not l
    assert len(l) == 0
    assert list(l) == []

    l.append(321)
    l.append(654)
    l.append(789)
    assert len(l) == 3
    assert list(l) == [321, 654, 789]

    l.append(987)
    assert len(l) == 3
    assert list(l) == [654, 789, 987]

    assert l[0] == l[-3] == 654
    assert l[1] == l[-2] == 789
    assert l[2] == l[-1] == 987

    assert l.pop() == 987
    assert len(l) == 2
    assert list(l) == [654, 789]

    assert l.pop_front() == 654
    assert len(l) == 1
    assert list(l) == [789]

    assert l.pop_front() == 789
    assert len(l) == 0
    assert list(l) == []
