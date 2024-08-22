from src.const import obelysk_dim
from src.entity import Entity


class Obelysk(Entity):

    def __init__(self, pos, race):
        super().__init__(pos, obelysk_dim)
        self._race = race

    def get_race(self):
        return self._race
