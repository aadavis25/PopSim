import math
import random
from typing import List, Optional, Self

from src.const import (
    genders,
    human_dim,
    interaction_delay,
    interact_dist,
    marry_chance,
    marry_gender,
    max_call,
    max_energy,
    see_dist,
    talking_to_max,
    want_to_see_ticks,
    max_target_ticks,
)
from src.entity import Entity
from src.house import House
from src.memory import Memory
from src.obelysk import Obelysk
from src.race import Race


class Human(Entity):
    def __init__(self, world, pos: List[int], personality: str, race: Race):
        super().__init__(pos, human_dim)
        self._world = world
        self._gender = random.choice(genders)
        self._personality = personality
        self._friends = set()
        self._know = set()
        self._can_see = set()
        self._spouse = None
        self._race = race
        self._energy = 3600
        self._napping = False
        self._house = None
        self.clear_target()
        self._memories = {}
        self._the_call = max_call
        self._inventory = []
        self.talking_to = [None, 0]
        self.max_interactions_per_tick = 1
        self._ticks_per_move = 2
        self._movement_ticks = 0

    def tick(self):
        self.look_around()
        self.interact()
        self.do_something()
        if self._the_call:
            self._the_call -= 1

    def interact(self):
        if self._energy <= 0:
            if self.talking_to[0]:
                self.stop_talking()
            return
        for i in range(0, min(self.max_interactions_per_tick, len(self._nearby))):
            if self._napping:
                return
            if self.talking_to[0]:
                if self.talking_to[1]:
                    self.talking_to[1] -= 1
                    self._energy -= 1
                    return
                else:
                    other = self.talking_to[0]
                    self.stop_talking()
                    self.add_memory(other)
                    self.add_known(other)
                    if self.can_be_friends(other):
                        self.add_friend(other)
                    if not self._spouse and not other._spouse:
                        if (
                            other in self._friends
                            and self.can_be_spouse(other)
                            and self.get_gender() == marry_gender
                            and random.randint(1, marry_chance) == marry_chance
                        ):
                            self.get_married(other)
            if self._target[0] in self._nearby:
                other = self._target[0]
                self.clear_target()
            else:
                other = random.choice(list(self._nearby))
            if (
                type(other) is Human
                and other is not self
                and not other.get_napping()
                and not other.calling()
                and not other.talking_to[0]
                and self.want_to_talk(other)
            ):
                self.stop_and_talk(other)
            if type(other) is Obelysk:
                if other is self._race.get_obelysk():
                    self._the_call = max_call
            if type(other) is House:
                if self._energy <= 0 and self._house and self.am_at_house():
                    self.nap()

    def clear_target(self):
        self._target = [None, 0]

    def get_married(self, other: Self):
        if self._spouse or other._spouse:
            return
        other.set_spouse(self)
        self.set_spouse(other)

    def build_house(self):
        house = House(self._race.get_obelysk().get_pos(), self)
        self._house = house
        if self._spouse:
            self._spouse._house = house
        self._world.put_entity(house)

    def look_around(self):
        self._can_see.clear()
        self._nearby.clear()
        pos = self.get_pos()

        for see_node in self._world.get_nodes_within(pos, see_dist):
            self._can_see.update(see_node.get_entities())
        self._can_see.discard(self)
        for nearby_node in self._world.get_nodes_within(pos, interact_dist):
            self._nearby.update(nearby_node.get_entities())
        self._nearby.discard(self)

    def do_something(self):
        if self._energy <= 0:
            if self.talking_to[0]:
                self.stop_talking()
            if self._house and self.am_at_house():
                self.nap()
                return
            self._target = [self._house or self.get_obelysk(), 0]
        elif self._napping and self._house and self.am_at_house():
            self.nap()
            return
        if self.talking_to[0]:
            return
        if (
            self._target[0]
            and self._target[1] >= max_target_ticks
            and type(self._target[0]) not in [Obelysk, House]
        ):
            self.clear_target()
        if self._energy > 0 and not self._the_call:
            self._target = [self.get_obelysk(), 0]
        if not self._target[0]:
            for e in self._can_see:
                if (
                    type(e) is Human
                    and not e.get_napping()
                    and e is not self
                    and e not in self._know
                    and not e.talking_to[0]
                ):
                    self._target = [e, 0]
                    self.summon(e)
                    break
        if self._target[0]:
            self._movement_ticks += 1
            if self._movement_ticks >= self._ticks_per_move:
                self.move_toward(self._target[0])
                self._movement_ticks = 0
            self._target[1] += 1
        else:
            for e in self._friends:
                mem = self.remember(e)
                if self._world.get_time() - mem.get_time() >= want_to_see_ticks:
                    self._target = [e, -9999]
                    break
        if not self._target[0]:
            self.walkabout()

    def summon(self, other: Self):
        other.set_target([self, 0])

    def move_rand(self):
        self._pos[0] += random.randint(-1, 1)
        self._pos[1] += random.randint(-1, 1)

    def move_toward(self, other_entity: Entity):
        pos = other_entity.get_pos()
        delta_x = self._pos[0] - pos[0]
        delta_y = self._pos[1] - pos[1]
        ratio = abs(delta_x / delta_y) if delta_y != 0 else math.inf
        if abs(delta_x) > 0 and ratio > 0.5:
            self._pos[0] -= (1 if delta_x > 0 else -1) if delta_x != 0 else 0
        if abs(delta_y) > 0 and ratio < 2:
            self._pos[1] -= (1 if delta_y > 0 else -1) if delta_y != 0 else 0

    def nap(self):
        self.stop_talking()
        self.clear_target()
        self._napping = True
        self._energy = min(max_energy, self._energy + 5)
        if self._energy >= max_energy:
            self._napping = False

    def add_memory(self, o: Entity):
        memory = self._memories.get(o)
        if memory:
            memory.set_time(self._world.get_time())
            return
        self._memories[o] = Memory(o, self._world.get_time())

    def remember(self, o: Entity) -> Optional[Memory]:
        return self._memories.get(o)

    def set_can_see(self, array):
        self._can_see = array

    def can_be_friends(self, other: Self) -> bool:
        return (self.get_personality().lower() == other.get_personality().lower()) and (
            self.get_race() is other.get_race()
            or random.randint(1, marry_chance) == marry_chance
        )

    def can_be_spouse(self, other: Self) -> bool:
        return (
            (self._personality == other.get_personality())
            and (self._gender != other.get_gender())
            and (self.get_race() is other.get_race())
        )

    def add_friend(self, other: Self):
        if other not in self._friends:
            self._friends.add(other)

    def add_known(self, other: Self):
        if other not in self._know:
            self._know.add(other)
            other._know.add(self)

    def stop_and_talk(self, other: Self):
        self.clear_target()
        other.clear_target()
        self.talking_to = [other, talking_to_max]
        other.talking_to = [self, talking_to_max]

    def stop_talking(self):
        if self.talking_to[0]:
            self.talking_to[0].talking_to = [None, 0]
            self.talking_to = [None, 0]

    def want_to_talk(self, other: Self) -> bool:
        memory = self.remember(other)
        return (
            not memory or self._world.get_time() - memory.get_time() > interaction_delay
        )

    def am_at_house(self) -> bool:
        if not self._house:
            return True
        elif self._house in self._world.get_at(self.get_pos()).get_entities():
            return True
        return False

    def set_spouse(self, other: Self):
        self._spouse = other

    def get_gender(self):
        return self._gender

    def get_personality(self):
        return self._personality

    def get_race(self):
        return self._race

    def get_target(self):
        return self._target

    def set_target(self, target: List[Entity | int]):
        self._target = target

    def get_energy(self):
        return self._energy

    def get_napping(self):
        return self._napping

    def get_obelysk(self):
        return self.get_race().get_obelysk()

    def walkabout(self):
        self._target = [self._world.get_random_entity(exclude=self), 0]

    def calling(self):
        return not self._the_call
