# world
import math
import random
from collections import deque
from typing import Iterator

from src.const import FOOD_NODES, obelysk_dim, personalities
from src.entity import Entity
from src.food_node import FoodNode
from src.human import Human
from src.obelysk import Obelysk
from src.race import Race
from src.world_square import WorldSquare

races = [Race('Blue', (0, 0, 255)), Race('Red', (255, 0, 0)),
         Race('Yellow', (255, 255, 0)), Race('Pearl', (192, 192, 192))]


def get_x(pos):
    return pos[0]


def get_y(pos):
    return pos[1]


class World:
    _world_dim = [500, 500]
    _world = None
    _entities = set()

    def __init__(self, width, height, people):
        self._world_dim[0] = width
        self._world_dim[1] = height
        self._world = [[WorldSquare([x, y]) for x in range(self._world_dim[0])] for y in
                       range(self._world_dim[1])]
        self._time = 0

        for i in range(people):
            human = Human(self,
                          self.random_pos(),
                          random.choice(personalities),
                          random.choice(races))
            self.get_at(human.get_pos()).append(human)
            self._entities.add(human)
        for i in range(FOOD_NODES):
            food_node = FoodNode(self.random_pos())
            self.put_entity(food_node)
        for race in races:
            o = Obelysk(self.random_pos(obelysk_dim), race)
            race.set_obelysk(o)
            self.put_entity(o)

    def random_pos(self, dim=None):
        if dim is None:
            dim = [1, 1]
        return [random.randint(0, self._world_dim[0] - (dim[0] + 1)),
                random.randint(0, self._world_dim[1] - (dim[1] + 1))]

    def valid_pos(self, x, y):
        return 0 <= x < self._world_dim[0] and 0 <= y < self._world_dim[1]

    def get_adjacent_nodes(self, pos):
        x, y = get_x(pos), get_y(pos)
        for neighbor_x in range(max(0, x - 1), min(self._world_dim[0] - 1, x + 1) + 1):
            for neighbor_y in range(max(0, y - 1), min(self._world_dim[1] - 1, y + 1) + 1):
                if neighbor_x != x or neighbor_y != y:
                    yield self._world[neighbor_y][neighbor_x]

    def find_first_neighbor(self, start_node, func, args):
        visited = {start_node}
        queue = deque([start_node])
        while queue:
            node = queue.popleft()
            for neighbor in self.get_adjacent_nodes(node.get_pos()):
                if neighbor in visited:
                    continue
                if func(neighbor, args):
                    return neighbor
                visited.add(neighbor)
                queue.append(neighbor)
        return None

    def do_tick(self, e):
        pos = e.get_pos()
        old = (get_x(pos), get_y(pos))
        e.tick()
        self.update(old, e)

    def update(self, old, thing):
        if thing in self.get_at(old).get_entities():
            self.get_at(old).remove(thing)
        new = thing.get_pos()
        self.get_at(new).append(thing)

    def tick(self):
        self._time += 1
        # pool = ThreadPool(10)
        # pool.map(self.do_tick, self._entities)
        for e in self._entities:
            self.do_tick(e)

    def put_entity(self, entity: Entity):
        self._entities.add(entity)
        pos = entity.get_pos()
        if not self.nothing_here(entity, entity.get_dim()):
            pos = self.find_first_neighbor(self.get_at(pos), self.nothing_here, entity.get_dim()).get_pos()
            entity.set_pos([get_x(pos), get_y(pos)])
        width, height = entity.get_dim()
        for x in range(get_x(pos), get_x(pos) + width):
            for y in range(get_y(pos), get_y(pos) + height):
                self.get_at([x, y]).append(entity)
        self._entities.add(entity)

    def nothing_here(self, entity, dim):
        pos = entity.get_pos()
        width, height = dim
        x, y = get_x(pos), get_y(pos)
        if not self.valid_pos(x, y) or not self.valid_pos(x + width - 1, y + height - 1):
            return False
        for cell_x in range(x, x + width):
            for cell_y in range(y, y + height):
                for e in self.get_at([cell_x, cell_y]).get_entities():
                    if type(e) is not Human:
                        return False
        return True

    def get_entities(self):
        return self._entities

    def get_dim(self):
        return self._world_dim

    def get_max_dim(self):
        return get_x(self._world_dim) - 1

    def get_time(self):
        return self._time

    def get_world_dim(self):
        return self._world_dim

    def get_at(self, pos) -> WorldSquare:
        return self._world[get_y(pos)][get_x(pos)]

    def get_random_entity(self):
        return random.choice(list(self._entities))

    def get_nodes_within(self, pos, dist) -> Iterator[WorldSquare]:
        x, y = get_x(pos), get_y(pos)
        min_x = max(0, math.ceil(x - dist))
        max_x = min(self._world_dim[0] - 1, math.floor(x + dist))
        min_y = max(0, math.ceil(y - dist))
        max_y = min(self._world_dim[1] - 1, math.floor(y + dist))
        for node_x in range(min_x, max_x + 1):
            for node_y in range(min_y, max_y + 1):
                if math.hypot(node_x - x, node_y - y) <= dist:
                    yield self._world[node_y][node_x]
