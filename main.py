import argparse
import time

import pygame as pg

import const
import house
import human
import obelysk
import world

i = 0
TITLE = "Grid"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 900
TILES_HORIZONTAL = int(WINDOW_WIDTH / 10)
TILES_VERTICAL = int(WINDOW_HEIGHT / 10)
TILE_SIZE = 100
PEOPLE = 200


class Game:
    def __init__(self, width, height, population):
        self.the_world = world.World(width, height, population)
        pg.init()
        self.clock = pg.time.Clock()
        pg.display.set_caption(TITLE)
        self.surface = pg.display.set_mode((width, height))
        self.loop = True

    def main(self):
        while self.loop:
            self.grid_loop()
        pg.quit()

    def grid_loop(self):
        self.the_world.tick()
        self.surface.fill((0, 0, 0))
        for row in range(TILES_HORIZONTAL):
            for col in range(row % 2, TILES_HORIZONTAL, 2):
                pg.draw.rect(
                    self.surface,
                    (40, 40, 40),
                    (row * TILE_SIZE, col * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                )
        for entity in self.the_world.get_entities():
            if type(entity) is human.Human:
                pg.draw.circle(self.surface,
                               entity.get_race().get_color(),
                               entity.get_pos(),
                               2)
            if type(entity) is house.House:
                pg.draw.rect(
                    self.surface,
                    (139, 69, 19),
                    (entity.get_pos()[0], entity.get_pos()[1], const.house_dim[0], const.house_dim[1]))
            if type(entity) is obelysk.Obelysk:
                pg.draw.rect(
                    self.surface,
                    entity.get_race().get_color(),
                    (entity.get_pos()[0], entity.get_pos()[1], 10, 10))

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.loop = False
        pg.display.update()
        time.sleep(1 / 30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("PopSim")
    parser.add_argument("-e", metavar="height", help="world height.", type=int)
    parser.add_argument("-w", metavar="width", help="world width.", type=int)
    parser.add_argument("-p", metavar="population", help="number of people.", type=int)
    args = parser.parse_args()
    mygame = Game(args.w or WINDOW_WIDTH, args.e or WINDOW_HEIGHT, args.p or PEOPLE)
    mygame.main()
