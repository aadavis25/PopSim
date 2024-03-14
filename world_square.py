class WorldSquare:
    def __init__(self, pos):
        self._pos = pos
        self._entities = []
        self._neighbors = []

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
