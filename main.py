import argparse
import logging
import time
from threading import Event, Lock, Thread

import pygame as pg

from src.const import (
    NANOSECONDS_PER_SECOND,
    PEOPLE,
    TICK_INTERVAL_NS,
    TITLE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from src.renderer import GridRenderer
from src.world import World


logger = logging.getLogger(__name__)


def positive_int(value):
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from error
    if result <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="PopSim")
    parser.add_argument(
        "-w", "--width", default=WINDOW_WIDTH, type=positive_int, help="world width"
    )
    parser.add_argument(
        "--height", default=WINDOW_HEIGHT, type=positive_int, help="world height"
    )
    parser.add_argument(
        "-p", "--population", default=PEOPLE, type=positive_int, help="number of people"
    )
    return parser.parse_args(argv)


class Game:
    def __init__(self, width, height, population):
        self.the_world = World(width, height, population)
        pg.init()
        pg.display.set_caption(TITLE)
        self.surface = pg.display.set_mode((width, height))
        self.renderer = GridRenderer(width, height)
        self.clock = pg.time.Clock()
        self.loop = True
        self._world_lock = Lock()
        self._world_error = None
        self.world_thread = None

    def main(self):
        stop_event = Event()
        self.loop = True
        self._world_error = None
        self.world_thread = Thread(
            target=self._run_world,
            args=(stop_event,),
            name="PopSim world",
            daemon=False,
        )
        self.world_thread.start()
        try:
            self.grid_loop(stop_event)
        finally:
            stop_event.set()
            self.world_thread.join()
            pg.quit()

        if self._world_error is not None:
            raise self._world_error

    def _run_world(self, stop_event):
        try:
            self.world_loop(stop_event)
        except Exception as error:
            self._world_error = error
            logger.exception("World thread failed")
            stop_event.set()

    def world_loop(self, stop_event, clock=None, wait=None):
        if clock is None:
            clock = time.perf_counter_ns
        if wait is None:
            wait = stop_event.wait

        while not stop_event.is_set():
            start = clock()
            with self._world_lock:
                self.the_world.tick()
            elapsed = clock() - start
            remaining = TICK_INTERVAL_NS - elapsed
            if remaining > 0:
                if not stop_event.is_set():
                    wait(remaining / NANOSECONDS_PER_SECOND)
            elif remaining < 0:
                logger.warning(
                    "World tick overran target by %.3f ms",
                    -remaining / 1_000_000,
                )

    def grid_loop(self, stop_event):
        while self.loop and not stop_event.is_set():
            with self._world_lock:
                entities = tuple(self.the_world.get_entities())
            self.renderer.draw(self.surface, entities)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.loop = False
                    break

            pg.display.flip()
            self.clock.tick(60)


def main(argv=None):
    args = parse_args(argv)
    Game(args.width, args.height, args.population).main()


if __name__ == "__main__":
    main()
