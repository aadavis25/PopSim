# entity


class Entity:
    def __init__(self, pos, dim=None):
        if dim is None:
            dim = [1, 1]
        self._pos = pos
        self._nearby = []
        self._dim = dim

    def interact(self):
        pass

    def tick(self):
        pass

    def get_pos(self):
        return self._pos

    def set_pos(self, pos):
        self._pos = pos

    def set_nearby(self, array):
        self._nearby = array

    def get_dim(self):
        return self._dim
