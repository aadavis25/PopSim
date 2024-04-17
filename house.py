import const
import entity


class House(entity.Entity):
    def __init__(self, pos, owner):
        newpos = [pos[0], pos[1]]
        super().__init__(newpos, const.house_dim)
        self._owner = owner
        self._dim = const.house_dim
