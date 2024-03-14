import entity


class Obelysk(entity.Entity):

    def __init__(self, pos, race):
        super().__init__(pos)
        self._race = race

    def get_race(self):
        return self._race
