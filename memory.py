class Memory:
    def __init__(self, entity, time):
        self._entity = entity
        self._time = time

    def get_entity(self):
        return self._entity

    def get_time(self):
        return self._time

    def set_time(self, time):
        self._time = time
