# PERSON
import math
import random

import const
import entity
import memory
import obelysk
from const import marry_chance, marry_gender
from house import House


class Human(entity.Entity):

    def __init__(self, world, pos, personality, race):
        super().__init__(pos)
        self._world = world
        self._gender = random.choice(const.genders)
        self._personality = personality
        self._friends = []
        self._know = []
        self._can_see = []
        self._spouse = None
        self._race = race
        self._energy = 100
        self._napping = False
        self._house = None
        self._target = [None, 0]
        self._memories = []
        self._the_call = 0

    def interact(self):
        for i in range(0, min(const.max_interactions_per_tick, len(self._nearby))):
            other = self._nearby[i]
            if self._target[0] in self._nearby:
                other = self._target[0]
                self._target = [None, 0]
            if type(other) is Human:
                self.add_memory(other)
                self.add_known(other)
                # print(
                #     self.get_personality() + " "
                #     + self.get_gender() + " interacting with "
                #     + other.get_personality() + " "
                #     + other.get_gender())
                if self.can_be_friends(other):
                    # print("FRIEND")
                    self.add_friend(other)
                if not self._spouse:
                    if (other in self._friends
                            and self.can_be_spouse(other)
                            and self.get_gender() == marry_gender
                            and random.randint(1, marry_chance) == marry_chance):
                        # print("MARRIAGE")
                        self.get_married(other)
            if type(other) is obelysk.Obelysk:
                if other is self._world.get_ob_for_race(self.get_race()):
                    self._the_call = 0

    def get_married(self, other):
        other.set_spouse(self)
        self.set_spouse(other)
        house = House(self._world.get_ob_for_race(self.get_race()).get_pos(), self)
        self._house = house
        other._house = house
        self._world.put_thing(house)

    def tick(self):
        self._the_call += 1
        if self._energy and not self.get_napping():
            # start = time.time()
            self.look_around()
            # stop = time.time()
            # print("1: " + str(stop - start))
            # start = time.time()
            self.interact()
            # stop = time.time()
            # print("2: " + str(stop - start))
            # start = time.time()
            self.whereto()
            # stop = time.time()
            # print("3: " + str(stop - start))
            self._energy -= 1
        else:
            self.nap()

    def look_around(self):
        self._can_see = []
        self._nearby = []
        for e in self._world.get_entities():
            dist = math.dist(self.get_pos(), e.get_pos())
            if dist < const.interact_dist:
                self._nearby.append(e)
            if dist < const.see_dist:
                self._can_see.append(e)

    def whereto(self):
        # print(str(self.get_pos()) + " move toward " + str(target.get_pos()))
        if self._target[0] and (self._target[1] == 300 or
                                const.how_far(self.get_pos(), self._target[0].get_pos()) > const.see_dist):
            self._target = [None, 0]
        if not self._target[0]:
            if self._the_call > const.max_call:
                self._target = [self._world.get_ob_for_race(self.get_race()), 0]
            else:
                # self.look_around()
                for e in self._can_see:
                    if type(e) is Human and not e.get_napping():
                        if e not in self._know:
                            self._target = [e, 0]
                            self.call(e)
                            break
                        else:
                            mem = self.remember(e)
                            if e in self._friends:
                                if self._world.get_time() - mem.get_time() >= const.want_to_see_ticks:
                                    self._target = self._world.get_ob_for_race(e.get_race())
                                    self.call(e)
                            if self._world.get_time() - mem.get_time() >= const.want_to_see_ticks * 10:
                                self._target = [e, 0]
                                self.call(e)
            # print(str(self.get_pos()) + " move rand")
        if self._target[0]:
            self.move_toward(self._target[0])
            self._target[1] += 1
        else:
            self.move_toward(self._world.get_ob_for_race(self.get_race()) if not self._house else self._house)
        self.validate_pos()

    def validate_pos(self):
        if self._pos[0] > self._world.get_max_dim():
            self._pos[0] = self._world.get_max_dim()
        if self._pos[1] > self._world.get_max_dim():
            self._pos[1] = self._world.get_max_dim()

    def call(self, other):
        other.set_target([self, 0])

    def move_rand(self):
        self._pos[0] += random.randint(-1, 1)
        self._pos[1] += random.randint(-1, 1)

    def move_toward(self, other_entity):
        pos = other_entity.get_pos()
        delta_x = self._pos[0] - pos[0]
        delta_y = self._pos[1] - pos[1]
        ratio = abs(delta_x / delta_y if delta_y != 0 else math.inf)
        if abs(delta_x) > 0 and ratio > .5:
            self._pos[0] -= (1 if delta_x > 0 else -1) if delta_x != 0 else 0
        if abs(delta_y) > 0 and ratio < 2:
            self._pos[1] -= (1 if delta_y > 0 else -1) if delta_y != 0 else 0

    def nap(self):
        self._napping = True
        self._energy += 5
        if self._energy == const.max_energy:
            self._napping = False

    def add_memory(self, o):
        for mem in self._memories:
            if mem.get_entity() is o:
                mem.set_time(self._world.get_time())
                return
        self._memories.append(memory.Memory(o, self._world.get_time()))

    def remember(self, o):
        for mem in self._memories:
            if mem.get_entity() is o:
                return mem
        return None

    def set_can_see(self, array):
        self._can_see = array

    def can_be_friends(self, other):
        return (self.get_personality().lower() == other.get_personality().lower()) and (
                self.get_race() is other.get_race() or random.randint(1, marry_chance) is marry_chance)

    def can_be_spouse(self, other):
        return (self._personality == other.get_personality()) and (self._gender != other.get_gender()) and (
                self.get_race() is other.get_race())

    def add_friend(self, other):
        if other not in self._friends:
            self._friends.append(other)

    def add_known(self, other):
        if other not in self._know:
            self._know.append(other)

    def set_spouse(self, other):
        self._spouse = other

    def get_gender(self):
        return self._gender

    def get_personality(self):
        return self._personality

    def get_race(self):
        return self._race

    def get_target(self):
        return self._target

    def set_target(self, target):
        self._target = target

    def get_energy(self):
        return self._energy

    def get_napping(self):
        return self._napping
