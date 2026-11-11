import logging
import random
import threading

import pygame as pg
import pytest
import main

from src.const import PEOPLE, WINDOW_HEIGHT, WINDOW_WIDTH, tick_speed_ns
from src.entity import Entity
from src.food_node import FoodNode
from src.house import House
from src.obelysk import Obelysk
from src.race import Race
from src import world as world_module
from src.world import World


class FakeWorld:
    def __init__(self, width, height, population):
        self.width = width
        self.height = height
        self.population = population
        self.entities = set()
        self.tick_count = 0
        self.on_tick = None

    def tick(self):
        self.tick_count += 1
        if self.on_tick:
            self.on_tick()

    def get_entities(self):
        return self.entities


class TrackedThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.join_calls = 0

    def join(self, *args, **kwargs):
        self.join_calls += 1
        return super().join(*args, **kwargs)


@pytest.fixture(autouse=True)
def pygame_headless(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    yield
    pg.quit()


def create_game(monkeypatch, world_type=FakeWorld, width=250, height=150):
    monkeypatch.setattr(main, "World", world_type)
    return main.Game(width, height, 0)


def track_threads(monkeypatch):
    threads = []

    def create_thread(*args, **kwargs):
        thread = TrackedThread(*args, **kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr(main, "Thread", create_thread)
    return threads


def test_parse_args_uses_defaults_and_long_height_option():
    args = main.parse_args([])

    assert (args.width, args.height, args.population) == (
        WINDOW_WIDTH, WINDOW_HEIGHT, PEOPLE,
    )
    args = main.parse_args(["--width", "320", "--height", "240", "--population", "7"])
    assert (args.width, args.height, args.population) == (320, 240, 7)


@pytest.mark.parametrize(
    "argv",
    [
        ["--width", "0"],
        ["--height", "-1"],
        ["--population", "0"],
        ["--width", "wide"],
    ],
)
def test_parse_args_rejects_nonpositive_or_noninteger_values(argv):
    with pytest.raises(SystemExit) as exc:
        main.parse_args(argv)
    assert exc.value.code == 2


def test_renderer_covers_window_with_correct_checkerboard_geometry():
    from src.renderer import GridRenderer

    renderer = GridRenderer(250, 150)
    surface = pg.Surface((250, 150))
    renderer.draw(surface, ())

    assert surface.get_size() == (250, 150)
    assert surface.get_at((0, 0))[:3] == (0, 85, 0)
    assert surface.get_at((100, 0))[:3] == (0, 125, 0)
    assert surface.get_at((0, 100))[:3] == (0, 125, 0)
    assert surface.get_at((249, 149))[:3] == (0, 125, 0)


def test_renderer_draws_entities_at_their_world_positions():
    from src.renderer import GridRenderer
    from src.human import Human

    race = Race("Blue", (0, 0, 255))
    entities = (
        Human(None, [20, 20], "A", race),
        House([40, 30], None),
        Obelysk([60, 30], race),
        FoodNode([80, 30]),
    )
    surface = pg.Surface((120, 100))
    GridRenderer(120, 100).draw(surface, entities)

    assert surface.get_at((20, 20))[:3] == race.get_color()
    assert surface.get_at((40, 30))[:3] == (139, 69, 19)
    assert surface.get_at((60, 30))[:3] == race.get_color()
    assert surface.get_at((80, 30))[:3] == (0, 200, 0)


def test_game_quit_renders_frames_caps_fps_and_joins_world_thread(monkeypatch):
    game = create_game(monkeypatch)
    threads = track_threads(monkeypatch)
    event_batches = iter(([], [], [pg.event.Event(pg.QUIT)]))
    monkeypatch.setattr(main.pg.event, "get", lambda: next(event_batches))
    rendered = []
    original_draw = game.renderer.draw

    def draw(surface, entities):
        rendered.append(entities)
        original_draw(surface, entities)

    monkeypatch.setattr(game.renderer, "draw", draw)

    class FrameClock:
        def __init__(self):
            self.calls = []

        def tick(self, fps):
            self.calls.append(fps)

    game.clock = FrameClock()
    game.main()

    assert len(rendered) == 3
    assert all(isinstance(snapshot, tuple) for snapshot in rendered)
    assert game.clock.calls == [60, 60, 60]
    assert len(threads) == 1
    assert threads[0].join_calls == 1
    assert not threads[0].is_alive()


def test_real_small_world_runs_headless_and_quits(monkeypatch):
    monkeypatch.setattr(world_module, "FOOD_NODES", 0)
    monkeypatch.setattr(World, "_world_dim", [500, 500])
    monkeypatch.setattr(World, "_entities", set())
    monkeypatch.setattr(world_module.random, "randint", random.Random(4).randint)
    game = main.Game(40, 50, 0)
    threads = track_threads(monkeypatch)
    event_batches = iter(([], [pg.event.Event(pg.QUIT)]))
    monkeypatch.setattr(main.pg.event, "get", lambda: next(event_batches))

    game.main()

    assert len(game.the_world.get_entities()) == 4
    assert threads[0].join_calls == 1
    assert not threads[0].is_alive()


def test_render_snapshot_is_taken_while_world_lock_is_held(monkeypatch):
    game = create_game(monkeypatch)
    threads = track_threads(monkeypatch)
    original_get_entities = game.the_world.get_entities

    def get_entities():
        assert game._world_lock.locked()
        return original_get_entities()

    tick_done = threading.Event()

    def add_entity():
        assert game._world_lock.locked()
        game.the_world.entities.add(Entity([1, 1]))
        tick_done.set()

    game.the_world.on_tick = add_entity
    monkeypatch.setattr(
        main.pg.event,
        "get",
        lambda: [pg.event.Event(pg.QUIT)] if tick_done.is_set() else [],
    )

    game.main()

    assert threads[0].join_calls == 1
    assert len(game.the_world.entities) >= 1


def test_world_thread_failure_is_logged_stops_and_reaches_caller(monkeypatch, caplog):
    class BrokenWorld(FakeWorld):
        def tick(self):
            raise RuntimeError("tick failure")

    game = create_game(monkeypatch, BrokenWorld)
    threads = track_threads(monkeypatch)
    monkeypatch.setattr(main.pg.event, "get", lambda: [])
    caplog.set_level(logging.ERROR)

    with pytest.raises(RuntimeError, match="tick failure"):
        game.main()

    assert threads[0].join_calls == 1
    assert not threads[0].is_alive()
    assert "World thread failed" in caplog.text


def test_render_failure_stops_and_joins_world_thread(monkeypatch):
    game = create_game(monkeypatch)
    threads = track_threads(monkeypatch)
    monkeypatch.setattr(
        game.renderer,
        "draw",
        lambda *_: (_ for _ in ()).throw(RuntimeError("render failure")),
    )

    with pytest.raises(RuntimeError, match="render failure"):
        game.main()

    assert threads[0].join_calls == 1
    assert not threads[0].is_alive()


def test_world_loop_waits_for_remaining_tick_budget():
    game = main.Game.__new__(main.Game)
    game._world_lock = threading.Lock()
    game.the_world = FakeWorld(10, 10, 0)
    stop_event = threading.Event()
    clock_values = iter((0, 10_000_000))
    waits = []

    def wait(seconds):
        waits.append(seconds)
        stop_event.set()

    game.world_loop(stop_event, clock=lambda: next(clock_values), wait=wait)

    assert game.the_world.tick_count == 1
    assert tick_speed_ns == pytest.approx(1_000_000_000 / 60)
    assert waits == pytest.approx([(tick_speed_ns - 10_000_000) / 1_000_000_000])


def test_world_loop_logs_overrun_without_sleeping(caplog):
    game = main.Game.__new__(main.Game)
    game._world_lock = threading.Lock()
    game.the_world = FakeWorld(10, 10, 0)
    stop_event = threading.Event()
    waits = []
    game.the_world.on_tick = stop_event.set
    clock_values = iter((0, 20_000_000))
    caplog.set_level(logging.WARNING)

    game.world_loop(
        stop_event,
        clock=lambda: next(clock_values),
        wait=waits.append,
    )

    assert waits == []
    assert "overran" in caplog.text.lower()


def test_world_loop_does_not_warn_or_wait_at_exact_tick_budget(caplog):
    game = main.Game.__new__(main.Game)
    game._world_lock = threading.Lock()
    game.the_world = FakeWorld(10, 10, 0)
    stop_event = threading.Event()
    game.the_world.on_tick = stop_event.set
    clock_values = iter((0, tick_speed_ns))
    waits = []
    caplog.set_level(logging.WARNING)

    game.world_loop(
        stop_event,
        clock=lambda: next(clock_values),
        wait=waits.append,
    )

    assert waits == []
    assert not caplog.records
