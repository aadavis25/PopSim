from types import SimpleNamespace

import pytest

from src.const import marry_chance, max_energy, marry_gender
from src.entity import Entity
from src.human import Human, HumanTarget
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
    human._target = HumanTarget(None, 0)
    human._the_call = 1
    human._can_see = set()
    human._friends = {friend}
    human._memories = {friend: Memory(friend, 0)}
    human._world = FakeWorld()
    human._pos = [0, 0]
    human.talking_to = [None, 0]
    human._ticks_per_move = 2
    human._movement_ticks = 0
    walkabout_calls = []
    monkeypatch.setattr(human, "walkabout", lambda: walkabout_calls.append(True))

    human.do_something()

    assert walkabout_calls == []
    assert human.get_target().entity is friend


def make_moving_human(monkeypatch):
    human = Human(None, [0, 0], "A", Race("Blue", (0, 0, 255)))
    human._world = FakeWorld()
    human._target = HumanTarget(Entity([10, 0]), 0)
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
    human._target = HumanTarget(None, 0)
    monkeypatch.setattr(human, "am_at_house", lambda: False)

    human.do_something()

    assert human.get_target().entity is home


def test_exhausted_human_without_home_returns_to_own_obelisk(monkeypatch):
    human = make_moving_human(monkeypatch)
    obelisk = Obelysk([10, 0], human.get_race())
    human.get_race().set_obelysk(obelisk)
    human._house = None
    human._energy = 0
    human._target = HumanTarget(None, 0)

    human.do_something()

    assert human.get_target().entity is obelisk


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
    assert human.get_target().entity is obelisk


def test_exhausted_human_at_home_restores_energy(monkeypatch):
    human = make_moving_human(monkeypatch)
    human._house = Entity([0, 0])
    human._energy = 0
    monkeypatch.setattr(human, "am_at_house", lambda: True)

    human.do_something()

    assert human.get_energy() == 5
    assert human.get_napping()


def test_home_rest_recovers_and_wakes_at_max_energy(monkeypatch):
    human = make_moving_human(monkeypatch)
    human._house = Entity([0, 0])
    human._energy = 0
    human._target = HumanTarget(None, 0)
    monkeypatch.setattr(human, "am_at_house", lambda: True)

    for _ in range(max_energy // 5):
        human.tick()

    assert human.get_energy() == max_energy
    assert not human.get_napping()


@pytest.mark.parametrize("busy_state", ["napping", "calling", "talking"])
def test_interact_does_not_start_conversation_with_busy_human(busy_state):
    race = Race("Blue", (0, 0, 255))
    human = Human(FakeWorld(), [0, 0], "A", race)
    target = Human(FakeWorld(), [1, 0], "A", race)
    old_target = HumanTarget(Entity([8, 8]), 12)
    target.set_target(old_target)
    if busy_state == "napping":
        target._napping = True
    elif busy_state == "calling":
        target._the_call = 0
    else:
        target.talking_to = [SimpleNamespace(), 5]

    human._nearby = {target}
    human.set_target(HumanTarget(target, 0))

    human.interact()

    assert human.talking_to == [None, 0]
    assert target.get_target() is old_target
    assert target.get_napping() is (busy_state == "napping")
    if busy_state == "talking":
        assert target.talking_to[0] is not None
    else:
        assert target.talking_to == [None, 0]


def test_interact_uses_can_be_friends_when_ending_conversation(monkeypatch):
    race = Race("Blue", (0, 0, 255))
    human = Human(FakeWorld(), [0, 0], "A", race)
    other = Human(FakeWorld(), [1, 0], "A", race)
    human._gender = "F"
    human.talking_to = [other, 0]
    other.talking_to = [human, 0]
    human._nearby = {other}
    calls = []
    monkeypatch.setattr(
        human, "can_be_friends", lambda candidate: calls.append(candidate) or True
    )

    human.interact()

    assert calls == [other]
    assert other in human._friends


def test_can_be_friends_uses_value_equality_for_chance(monkeypatch):
    class Chance(int):
        pass

    human = Human(FakeWorld(), [0, 0], "A", Race("Blue", (0, 0, 255)))
    other = Human(FakeWorld(), [1, 0], "a", Race("Red", (255, 0, 0)))
    monkeypatch.setattr("src.human.random.randint", lambda *_: Chance(marry_chance))

    assert human.can_be_friends(other)


def test_interact_does_not_marry_an_already_married_target(monkeypatch):
    race = Race("Blue", (0, 0, 255))
    human = Human(FakeWorld(), [0, 0], "A", race)
    other = Human(FakeWorld(), [1, 0], "A", race)
    other_spouse = Human(FakeWorld(), [2, 0], "B", race)
    human._gender = marry_gender
    other._gender = "F" if marry_gender == "M" else "M"
    human._friends.add(other)
    other._spouse = other_spouse
    human.talking_to = [other, 0]
    other.talking_to = [human, 0]
    human._nearby = {other}
    monkeypatch.setattr("src.human.random.randint", lambda *_: 20)

    human.interact()

    assert human._spouse is None
    assert other._spouse is other_spouse


def test_get_married_does_not_replace_an_existing_spouse():
    race = Race("Blue", (0, 0, 255))
    human = Human(FakeWorld(), [0, 0], "A", race)
    other = Human(FakeWorld(), [1, 0], "A", race)
    other_spouse = Human(FakeWorld(), [2, 0], "B", race)
    other._spouse = other_spouse

    human.get_married(other)

    assert human._spouse is None
    assert other._spouse is other_spouse


def test_nap_clamps_energy_and_wakes_when_recovery_overshoots():
    human = Human(FakeWorld(), [0, 0], "A", Race("Blue", (0, 0, 255)))
    human._energy = max_energy - 3
    human._napping = True

    human.nap()

    assert human.get_energy() == max_energy
    assert not human.get_napping()


def test_look_around_excludes_self_from_visible_and_nearby():
    human = Human(None, [0, 0], "A", Race("Blue", (0, 0, 255)))
    other = Entity([1, 0])
    square = SimpleNamespace(get_entities=lambda: {human, other})
    human._world = SimpleNamespace(get_nodes_within=lambda *_: [square])

    human.look_around()

    assert human not in human._can_see
    assert human not in human._nearby
    assert other in human._can_see
    assert other in human._nearby


def test_add_memory_updates_existing_memory_without_duplicates():
    time = [10]
    human = Human(
        SimpleNamespace(get_time=lambda: time[0]),
        [0, 0],
        "A",
        Race("Blue", (0, 0, 255)),
    )
    entity = Entity([1, 1])

    human.add_memory(entity)
    memory = human.remember(entity)
    time[0] = 20
    human.add_memory(entity)

    assert human.remember(entity) is memory
    assert memory.get_time() == 20
    assert human.remember(Entity([1, 1])) is None


def test_human_target_exposes_named_fields():
    human = Human(FakeWorld(), [0, 0], "A", Race("Blue", (0, 0, 255)))
    entity = Entity([1, 1])

    human.set_target(HumanTarget(entity, 7))

    assert isinstance(human.get_target(), tuple)
    assert human.get_target().entity is entity
    assert human.get_target().age == 7
