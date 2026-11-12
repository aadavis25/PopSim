import pygame as pg

from src.const import TILE_SIZE
from src.food_node import FoodNode
from src.house import House
from src.human import Human
from src.obelysk import Obelysk


class GridRenderer:
    def __init__(self, width, height):
        self._background = pg.Surface((width, height))
        for row, y in enumerate(range(0, height, TILE_SIZE)):
            for column, x in enumerate(range(0, width, TILE_SIZE)):
                color = (0, 85, 0) if (row + column) % 2 == 0 else (0, 125, 0)
                pg.draw.rect(
                    self._background,
                    color,
                    (x, y, min(TILE_SIZE, width - x), min(TILE_SIZE, height - y)),
                )

    def draw(self, surface, entities):
        surface.blit(self._background, (0, 0))
        for entity in entities:
            pos = entity.get_pos()
            if isinstance(entity, Human):
                if entity.calling():
                    pg.draw.circle(surface, (255, 255, 0), pos, 3)
                pg.draw.circle(surface, entity.get_race().get_color(), pos, 2)
            elif isinstance(entity, House):
                pg.draw.rect(surface, (139, 69, 19), (*pos, *entity.get_dim()))
            elif isinstance(entity, Obelysk):
                pg.draw.rect(
                    surface, entity.get_race().get_color(), (*pos, *entity.get_dim())
                )
            elif isinstance(entity, FoodNode):
                pg.draw.rect(surface, (0, 200, 0), (*pos, *entity.get_dim()))
