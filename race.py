class Race:
    def __init__(self, name, color):
        self._name = name
        self._color = color
        self._obelysk = None

    def get_name(self):
        return self._name

    def get_color(self):
        return self._color

    def get_obelysk(self):
        return self._obelysk

    def set_obelysk(self, ob):
        self._obelysk = ob
