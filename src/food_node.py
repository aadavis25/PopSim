from src.const import food_dim
from src.entity import Entity


class FoodNode(Entity):
    def __init__(self, pos):
        super().__init__(pos, food_dim)
