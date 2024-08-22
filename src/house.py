from typing import List

import src.const as const
import src.entity as entity


class House(entity.Entity):
    def __init__(self, pos: List[int], owner):
        new_pos = [pos[0], pos[1]]
        super().__init__(new_pos, const.house_dim)
        self._owner = owner
        self._dim = const.house_dim
        self.items = []
