import const
import entity


class Obelysk(entity.Entity):

    def __init__(self, pos, race):
        super().__init__(pos, const.obelysk_dim)
        self._race = race

    def get_race(self):
        return self._race
