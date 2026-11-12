from types import SimpleNamespace

from src.entity import Entity
from src.human import Human
from src.memory import Memory
from src.obelysk import Obelysk
from src.race import Race


class FakeWorld:
    def get_time(self):
        return 100_000


def test_do_something_retargets_friend_from_old_memory(monkeypatch):
    human = Human.__new__(Human)
    friend = Entity([5, 0])
    human._energy = 1
    human._napping = False
    human._house = None
    human._target = [None, 0]
    human._the_call = 1
    human._can_see = set()
    human._friends = {friend}
    human._memories = {Memory(friend, 0)}
    human._world = FakeWorld()
    human._pos = [0, 0]
    human.talking_to = [None, 0]
    human._ticks_per_move = 2
    human._movement_ticks = 0
    walkabout_calls = []
    monkeypatch.setattr(human, "walkabout", lambda: walkabout_calls.append(True))

    human.do_something()

    assert walkabout_calls == []
    assert human.get_target()[0] is friend


def make_moving_human(monkeypatch):
    human = Human(None, [0, 0], "A", Race("Blue", (0, 0, 255)))
    human._world = FakeWorld()
    human._target = [Entity([10, 0]), 0]
    monkeypatch.setattr(human, "look_around", lambda: None)
    monkeypatch.setattr(human, "interact", lambda: None)
    return human


def test_human_moves_every_two_ticks_at_normal_rate(monkeypatch):
    human = make_moving_human(monkeypatch)

    human.tick()
    assert human.get_pos() == [0, 0]

    human.tick()
    assert human.get_pos() == [1, 0]

    human.tick()
    assert human.get_pos() == [1, 0]

    human.tick()
    assert human.get_pos() == [2, 0]


def test_faster_human_moves_once_each_tick(monkeypatch):
    human = make_moving_human(monkeypatch)
    human._ticks_per_move = 1

    human.tick()
    assert human.get_pos() == [1, 0]

    human.tick()
    assert human.get_pos() == [2, 0]


def test_movement_does_not_drain_energy(monkeypatch):
    human = make_moving_human(monkeypatch)
    human._energy = 7

    human.tick()

    assert human.get_energy() == 7


def test_talking_spends_energy_per_active_tick():
    human = Human(FakeWorld(), [0, 0], "A", Race("Blue", (0, 0, 255)))
    partner = SimpleNamespace(talking_to=[human, 2])
    human._nearby = {Entity([0, 0])}
    human.talking_to = [partner, 2]
    human._energy = 5

    human.interact()

    assert human.get_energy() == 4
    assert human.talking_to[1] == 1


def test_exhausted_human_returns_to_home(monkeypatch):
    human = make_moving_human(monkeypatch)
    home = Entity([10, 0])
    human._house = home
    human._energy = 0
    human._target = [None, 0]
    monkeypatch.setattr(human, "am_at_house", lambda: False)

    human.do_something()

    assert human.get_target()[0] is home


def test_exhausted_human_without_home_returns_to_own_obelisk(monkeypatch):
    human = make_moving_human(monkeypatch)
    obelisk = Obelysk([10, 0], human.get_race())
    human.get_race().set_obelysk(obelisk)
    human._house = None
    human._energy = 0
    human._target = [None, 0]

    human.do_something()

    assert human.get_target()[0] is obelisk


def test_talking_exhaustion_ends_conversation_and_returns_to_obelisk(monkeypatch):
    race = Race("Blue", (0, 0, 255))
    obelisk = Obelysk([10, 0], race)
    race.set_obelysk(obelisk)
    human = Human(FakeWorld(), [0, 0], "A", race)
    partner = SimpleNamespace(talking_to=[human, 1])
    human._nearby = {Entity([0, 0])}
    human.talking_to = [partner, 1]
    human._energy = 1
    monkeypatch.setattr(human, "look_around", lambda: None)

    human.tick()

    assert human.get_energy() == 0
    assert human.talking_to == [None, 0]
    assert partner.talking_to == [None, 0]
    assert human.get_target()[0] is obelisk


def test_exhausted_human_at_home_restores_energy(monkeypatch):
    human = make_moving_human(monkeypatch)
    human._house = Entity([0, 0])
    human._energy = 0
    monkeypatch.setattr(human, "am_at_house", lambda: True)

    human.do_something()

    assert human.get_energy() == 5
    assert human.get_napping()
