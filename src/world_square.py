from typing import Set

from src.entity import Entity


class WorldSquare:
    def __init__(self, pos):
        self._pos = pos
        self._entities = set()

    def get_entities(self) -> Set[Entity]:
        return self._entities

    def append(self, entity):
        self._entities.add(entity)

    def remove(self, entity):
        self._entities.remove(entity)

    def get_pos(self):
        return self._pos
