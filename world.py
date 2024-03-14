# world
import random
from collections import deque

import const
import human
import obelysk
import world_square


class World:
    _world_dim = [500, 500]
    _world = None
    _entities = []

    def __init__(self, width, height, people):
        self._time = 0
        self._world_dim[0] = width
        self._world_dim[1] = height
        self._world = [[world_square.WorldSquare([x, y]) for x in range(self._world_dim[0])] for y in range(self._world_dim[1])]
        for x in range(self._world_dim[0]):
            for y in range(self._world_dim[1]):
                neighbors = []
                for i in range(x - 1, x + 2):
                    for j in range(y - 1, y + 2):
                        if self.valid_pos(i, j) and not (x == i and y == j):
                            neighbors.append(self.get_at([i, j]))
                self.get_at([x, y]).set_neighbors(neighbors)

        for i in range(people):
            thing = human.Human(self,
                                [random.randint(0, self._world_dim[0] - 1), random.randint(0, self._world_dim[1] - 1)],
                                random.choice(const.personalities),
                                random.choice(const.races))
            self._entities.append(thing)
            pos = thing.get_pos()
            self._world[pos[0]][pos[1]].append(thing)
        self._obs = [obelysk.Obelysk([0, 0], const.races[0]),
                     obelysk.Obelysk([0, self._world_dim[0] - 11], const.races[1]),
                     obelysk.Obelysk([self._world_dim[0] - 11, 0], const.races[2]),
                     obelysk.Obelysk([self._world_dim[0] - 11, self._world_dim[0] - 11], const.races[3])]
        for ob in self._obs:
            self.get_at(ob.get_pos()).append(ob)
            self._entities.append(ob)

    def valid_pos(self, x, y):
        return 0 <= x < self._world_dim[0] and 0 <= y < self._world_dim[1]

    def update(self, old, thing):
        if thing in self.get_at(old).get_entities():
            self.get_at(old).remove(thing)
        new = thing.get_pos()
        self.get_at(new).append(thing)

    def tick(self):
        self._time += 1
        for e in self._entities:
            old = e.get_pos()
            e.tick()
            self.update(old, e)
        # print("tick")

    def put_thing(self, entity):
        pos = entity.get_pos()
        if self.anything_here(entity.get_pos(), entity.get_dim()):
            pos = self.bfs(self.get_at(pos), entity.get_dim()).get_pos()
            entity.set_pos([pos[0], pos[1]])
        for i in range(pos[0], pos[0] + entity.get_dim()[0]):
            for j in range(pos[1], pos[1] + entity.get_dim()[1]):
                self.get_at([i, j]).append(entity)
        self._entities.append(entity)

    def anything_here(self, pos, dim):
        if self.valid_pos(pos[0] + dim[0], pos[1] + dim[1]):
            for i in range(pos[0], pos[0] + dim[0]):
                for j in range(pos[1], pos[1] + dim[1]):
                    if len(self.get_at([i, j]).get_entities()) > 0:
                        return True
        return False

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

    def get_at(self, pos):
        return self._world[pos[0]][pos[1]]

    def get_ob_for_race(self, race):
        for ob in self._obs:
            if ob.get_race() is race:
                return ob

    def bfs(self, start_node, dim):
        visited = set()
        queue = deque()
        visited.add(start_node)
        queue.append(start_node)
        while queue:
            m = queue.popleft()
            for neighbour in m.get_neighbors():
                if neighbour not in visited:
                    if not self.anything_here(neighbour.get_pos(), dim):
                        return neighbour
                    visited.add(neighbour)
                    queue.append(neighbour)

        return None
