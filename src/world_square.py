from typing import Set

from entity import Entity


class WorldSquare:
    def __init__(self, pos):
        self._pos = pos
        self._entities = set()
        self._neighbors = set()
        self._see_from_here = set()
        self._interact_from_here = set()

    def get_entities(self) -> Set[Entity]:
        return self._entities

    def get_neighbors(self):
        return self._neighbors

    def set_neighbors(self, neighbors):
        self._neighbors = neighbors

    def get_see_from_here(self):
        return self._see_from_here

    def set_see_from_here(self, list):
        self._see_from_here = list

    def get_interact_from_here(self):
        return self._interact_from_here

    def set_interact_from_here(self, list):
        self._interact_from_here = list

    def append(self, entity):
        self._entities.add(entity)

    def remove(self, entity):
        self._entities.remove(entity)

    def get_pos(self):
        return self._pos
