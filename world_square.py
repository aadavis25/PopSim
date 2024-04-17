class WorldSquare:
    def __init__(self, pos):
        self._pos = pos
        self._entities = []
        self._neighbors = []
        self._see_from_here = []
        self._interact_from_here = []

    def get_entities(self):
        return self._entities

    def get_neighbors(self):
        return self._neighbors

    def set_neighbors(self, neighbors):
        self._neighbors = neighbors

    def append(self, entity):
        self._entities.append(entity)

    def remove(self, entity):
        self._entities.remove(entity)

    def get_pos(self):
        return self._pos

    def get_see_from_here(self):
        return self._see_from_here

    def set_see_from_here(self, list):
        self._see_from_here = list

    def get_interact_from_here(self):
        return self._interact_from_here

    def set_interact_from_here(self, list):
        self._interact_from_here = list
