# world
import json
import random
from json import JSONDecodeError
from typing import List

from scipy.spatial import KDTree

from src.const import find_first_neighbor, FOOD_NODES, interact_dist, obelysk_dim, personalities, see_dist
from src.entity import Entity
from src.food_node import FoodNode
from src.human import Human
from src.obelysk import Obelysk
from src.race import Race
from src.world_square import WorldSquare

races = [Race('Blue', (0, 0, 255)), Race('Red', (255, 0, 0)),
         Race('Yellow', (255, 255, 0)), Race('Pearl', (192, 192, 192))]


def encode_poss(poss: List[List[int]]) -> List[List[int]]:
    y_to_x_map = {}
    for pos in poss:
        if pos[1] in y_to_x_map:
            if pos[0] < y_to_x_map[pos[1]][0]:
                y_to_x_map[pos[1]][0] = pos[0]
            if pos[0] > y_to_x_map[pos[1]][1]:
                y_to_x_map[pos[1]][1] = pos[0]
        else:
            y_to_x_map[pos[1]] = [pos[0], pos[0], pos[1]]
    return list(y_to_x_map.values())


def decode_poss(encoded_poss: List[List[int]]) -> List[List[int]]:
    decoded_poss = []
    for encoded_pos in encoded_poss:
        for i in range(encoded_pos[0], encoded_pos[1] + 1):
            decoded_poss.append([i, encoded_pos[2]])
    return decoded_poss


class World:
    _world_dim = [500, 500]
    _world = None
    _coords = None
    _tree = None
    _entities = set()

    def __init__(self, width, height, people):
        self._world_dim[0] = width
        self._world_dim[1] = height
        self._world = [[WorldSquare([x, y]) for y in range(self._world_dim[0])] for x in
                       range(self._world_dim[1])]
        self._coords = []
        for x in range(self._world_dim[0]):
            for y in range(self._world_dim[1]):
                self._coords.append([x, y])
        self._tree = KDTree(self._coords)
        self.make_world_paths()
        self._time = 0

        # print('Working on x: %d \r' % x, end='')

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

    def do_tick(self, e):
        old = (e.get_pos()[0], e.get_pos()[1])
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
            pos = find_first_neighbor(self.get_at(pos), self.nothing_here, entity.get_dim()).get_pos()
            entity.set_pos([pos[0], pos[1]])
        for i in range(pos[0], pos[0] + entity.get_dim()[0]):
            for j in range(pos[1], pos[1] + entity.get_dim()[1]):
                self.get_at([i, j]).append(entity)
        self._entities.add(entity)

    def nothing_here(self, entity, dim):
        pos = entity.get_pos()
        if self.valid_pos(pos[0] + dim[0], pos[1] + dim[1]):
            for i in range(pos[0], pos[0] + dim[0]):
                for j in range(pos[1], pos[1] + dim[1]):
                    for e in self.get_at([i, j]).get_entities():
                        if type(e) is not Human:
                            return False
        return True

    def get_entities(self):
        return self._entities

    def get_dim(self):
        return self._world_dim

    def get_max_dim(self):
        return self._world_dim[0] - 1

    def get_time(self):
        return self._time

    def get_world_dim(self):
        return self._world_dim

    def get_at(self, pos) -> WorldSquare:
        return self._world[pos[0]][pos[1]]

    def get_random_entity(self):
        return random.choice(list(self._entities))

    def get_nodes_within(self, pos, dist) -> List[WorldSquare]:
        points = self.get_points_within(pos, dist)
        ret = []
        for p in points:
            ret.append(self.get_at(self._coords[p]))
        return ret

    def get_points_within(self, pos, dist):
        return self._tree.query_ball_point(pos, dist)

    def make_world_paths(self):
        if not self.read_from_path_map():
            print("making world paths from scratch")
            for x in range(self._world_dim[0]):
                for y in range(self._world_dim[1]):
                    neighbors = []
                    for i in range(x - 1, x + 2):
                        for j in range(y - 1, y + 2):
                            if self.valid_pos(i, j) and not (x == i and y == j):
                                neighbors.append(self.get_at([i, j]))
                    self.get_at([x, y]).set_neighbors(neighbors)
                    self.get_at([x, y]).set_see_from_here(self.get_nodes_within([x, y], see_dist))
                    self.get_at([x, y]).set_interact_from_here(self.get_nodes_within([x, y], interact_dist))
            self.write_path_map()

    def write_path_map(self):
        path_map_file = open("cfg/path_map.json", "w+")
        path_str = "{"
        for x in range(self._world_dim[0]):
            for y in range(self._world_dim[1]):
                path_str += (f"\"[{x},{y}]\":{{"
                             f"\"neighbors\":{encode_poss([n.get_pos() for n in self.get_at([x, y]).get_neighbors()])},"
                             f"\"see\":{encode_poss([n.get_pos() for n in self.get_at([x, y]).get_see_from_here()])},"
                             f"\"interact\":{encode_poss([n.get_pos() for n in self.get_at([x, y]).get_interact_from_here()])}"
                             f"}},\n")
        path_str = path_str[0:-2] + "}"
        path_map_file.write(path_str)
        path_map_file.close()

    def read_from_path_map(self) -> bool:
        try:
            path_map_file = open("cfg/path_map.json")
            if path_map_file:
                path_map_json = json.load(path_map_file)
                if len(path_map_json.items()) != self._world_dim[0] * self._world_dim[1]:
                    return False
                for coords, attrs in path_map_json.items():
                    self.get_at(json.loads(coords)).set_neighbors(
                        [self.get_at(pos) for pos in decode_poss(attrs.get("neighbors"))])
                    self.get_at(json.loads(coords)).set_see_from_here(
                        [self.get_at(pos) for pos in decode_poss(attrs.get("see"))])
                    self.get_at(json.loads(coords)).set_interact_from_here(
                        [self.get_at(pos) for pos in decode_poss(attrs.get("interact"))])
                return True
        except (FileNotFoundError, JSONDecodeError):
            return False
