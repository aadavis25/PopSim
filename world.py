# world
import random
import time

from scipy.spatial import KDTree

import const
import human
import obelysk
import world_square


class World:
    _world_dim = [500, 500]
    _world = None
    _coords = None
    _tree = None
    _entities = []

    def __init__(self, width, height, people):
        self._time = 0
        self._world_dim[0] = width
        self._world_dim[1] = height
        self._world = [[world_square.WorldSquare([x, y]) for y in range(self._world_dim[0])] for x in range(self._world_dim[1])]
        self._coords = []
        for x in range(self._world_dim[0]):
            for y in range(self._world_dim[1]):
                self._coords.append([x, y])
        self._tree = KDTree(self._coords)
        for x in range(self._world_dim[0]):
            for y in range(self._world_dim[1]):
                neighbors = []
                for i in range(x - 1, x + 2):
                    for j in range(y - 1, y + 2):
                        if self.valid_pos(i, j) and not (x == i and y == j):
                            neighbors.append(self.get_at([i, j]))
                self.get_at([x, y]).set_neighbors(neighbors)
                # self.get_at([x, y]).set_see_from_here(self.get_nodes_within([x, y], const.see_dist))
                # self.get_at([x, y]).set_interact_from_here(self.get_nodes_within([x, y], const.interact_dist))

            # print('Working on x: %d \r' % x, end='')

        for i in range(people):
            thing = human.Human(self,
                                [random.randint(0, self._world_dim[0] - 1), random.randint(0, self._world_dim[1] - 1)],
                                random.choice(const.personalities),
                                random.choice(const.races))
            self._entities.append(thing)
            pos = thing.get_pos()
            self.get_at(pos).append(thing)
            const.races[0].set_obelysk(
                obelysk.Obelysk([random.randint(0, self._world_dim[0] - 1), random.randint(0, self._world_dim[1] - 1)],
                                const.races[0]))
            const.races[1].set_obelysk(
                obelysk.Obelysk([random.randint(0, self._world_dim[0] - 1), random.randint(0, self._world_dim[1] - 1)],
                                const.races[1]))
            const.races[2].set_obelysk(
                obelysk.Obelysk([random.randint(0, self._world_dim[0] - 1), random.randint(0, self._world_dim[1] - 1)],
                                const.races[2]))
            const.races[3].set_obelysk(
                obelysk.Obelysk([random.randint(0, self._world_dim[0] - 1), random.randint(0, self._world_dim[1] - 1)],
                                const.races[3]))
        for race in const.races:
            self.put_thing(race.get_obelysk())

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
        start = time.time_ns()

        # pool = ThreadPool(10)
        # pool.map(self.do_tick, self._entities)
        for e in self._entities:
            self.do_tick(e)
        print(self._time)
        stop = time.time_ns()
        wait = const.tick_speed_ns - (stop - start)
        if wait > 0:
            print("waiting" + str(wait / 1000000000))
            time.sleep(wait / 1000000000)
        self._time += 1

    def put_thing(self, entity):
        pos = entity.get_pos()
        if not self.nothing_here(entity, entity.get_dim()):
            pos = const.find_first_neighbor(self.get_at(pos), self.nothing_here, entity.get_dim()).get_pos()
            entity.set_pos([pos[0], pos[1]])
        for i in range(pos[0], pos[0] + entity.get_dim()[0]):
            for j in range(pos[1], pos[1] + entity.get_dim()[1]):
                self.get_at([i, j]).append(entity)
        self._entities.append(entity)

    def nothing_here(self, entity, dim):
        pos = entity.get_pos()
        if self.valid_pos(pos[0] + dim[0], pos[1] + dim[1]):
            for i in range(pos[0], pos[0] + dim[0]):
                for j in range(pos[1], pos[1] + dim[1]):
                    for e in self.get_at([i, j]).get_entities():
                        if type(e) is not human.Human:
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

    def get_at(self, pos):
        return self._world[pos[0]][pos[1]]

    def get_nodes_within(self, pos, dist):
        points = self.get_points_within(pos, dist)
        ret = []
        for p in points:
            ret.append(self.get_at(self._coords[p]))
        return ret

    def get_points_within(self, pos, dist):
        return self._tree.query_ball_point(pos, dist)
