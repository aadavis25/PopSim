import argparse
import time
from threading import Event, Thread

import pygame as pg

from src.const import ONE_MILLION, PEOPLE, tick_speed_ns, TILE_SIZE, TILES_HORIZONTAL, TILES_VERTICAL, TITLE, \
    WINDOW_HEIGHT, WINDOW_WIDTH
from src.food_node import FoodNode
from src.house import House
from src.human import Human
from src.obelysk import Obelysk
from src.world import World


class Game:

    def __init__(self, width, height, population):
        self.the_world = World(width, height, population)
        pg.init()
        self.clock = pg.time.Clock()
        pg.display.set_caption(TITLE)
        self.surface = pg.display.set_mode((width, height))
        self.loop = True

    def main(self):
        world_event = Event()
        world_thread = Thread(target=self.world_loop, args=[world_event])
        world_thread.start()

        self.grid_loop(world_event)

    def world_loop(self, event):
        tick = 0
        while not event.is_set():
            start = time.time_ns()

            self.the_world.tick()

            stop = time.time_ns()
            wait = tick_speed_ns - (stop - start)
            if wait > 0:
                print(f"{tick} waiting: {(wait / ONE_MILLION):0.3f}")
                time.sleep(wait / ONE_MILLION)
            tick += 1

    def grid_loop(self, world_event):
        while self.loop:
            self.surface.fill((0, 0, 0))
            for row in range(TILES_VERTICAL):
                for col in range(TILES_HORIZONTAL):
                    if (row + col) % 2 == 0:
                        pg.draw.rect(
                            self.surface,
                            (0, 85, 0),
                            (row * TILE_SIZE, col * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                        )
                    else:
                        pg.draw.rect(
                            self.surface,
                            (0, 125, 0),
                            (row * TILE_SIZE, col * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                        )
            for entity in self.the_world.get_entities():
                if type(entity) is Human:
                    if entity.calling():
                        pg.draw.circle(self.surface,
                                       (255, 255, 0),
                                       entity.get_pos(),
                                       3)
                    pg.draw.circle(self.surface,
                                   entity.get_race().get_color(),
                                   entity.get_pos(),
                                   2)
                if type(entity) is House:
                    pg.draw.rect(
                        self.surface,
                        (139, 69, 19),
                        (entity.get_pos()[0], entity.get_pos()[1], entity.get_dim()[0], entity.get_dim()[1]))
                if type(entity) is Obelysk:
                    pg.draw.rect(
                        self.surface,
                        entity.get_race().get_color(),
                        (entity.get_pos()[0], entity.get_pos()[1], entity.get_dim()[0], entity.get_dim()[1]))
                if type(entity) is FoodNode:
                    pg.draw.rect(
                        self.surface,
                        (0, 200, 0),
                        (entity.get_pos()[0], entity.get_pos()[1], entity.get_dim()[0], entity.get_dim()[1]))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.loop = False
                    world_event.set()
            pg.display.update()
        pg.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("PopSim")
    parser.add_argument("-i", metavar="height", help="world height.", type=int)
    parser.add_argument("-w", metavar="width", help="world width.", type=int)
    parser.add_argument("-p", metavar="population", help="number of people.", type=int)
    args = parser.parse_args()
    mygame = Game(args.w or WINDOW_WIDTH, args.i or WINDOW_HEIGHT, args.p or PEOPLE)
    mygame.main()
