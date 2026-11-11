import random

from src import world as world_module
from src.entity import Entity
from src.race import Race
from src.world import World
from src.world_square import WorldSquare


class MovingEntity(Entity):
    def __init__(self, pos, next_pos=None, dim=None):
        super().__init__(pos, dim)
        self.next_pos = next_pos
        self.tick_count = 0

    def tick(self):
        self.tick_count += 1
        if self.next_pos is not None:
            self.set_pos(self.next_pos)


def make_world(width=6, height=7):
    world = World.__new__(World)
    world._world_dim = [width, height]
    world._world = [
        [WorldSquare([x, y]) for x in range(width)]
        for y in range(height)
    ]
    world._entities = set()
    world._time = 0
    return world


def positions(nodes):
    return {tuple(node.get_pos()) for node in nodes}


def test_coordinate_accessors_name_width_and_height_axes():
    assert world_module.get_x([3, 7]) == 3
    assert world_module.get_y([3, 7]) == 7


def test_constructor_builds_height_rows_and_width_columns_and_registers_population(monkeypatch):
    monkeypatch.setattr(world_module, "FOOD_NODES", 0)
    monkeypatch.setattr(World, "_world_dim", [500, 500])
    monkeypatch.setattr(World, "_entities", set())
    monkeypatch.setattr(World, "random_pos", lambda self, dim=None: [2, 3])
    monkeypatch.setattr(World, "put_entity", lambda self, entity: None)
    monkeypatch.setattr(
        world_module,
        "races",
        [Race("Blue", (0, 0, 255)), Race("Red", (255, 0, 0))],
    )

    world = World(12, 14, 2)

    assert len(world._world) == 14
    assert all(len(row) == 12 for row in world._world)
    assert world.get_world_dim() == [12, 14]
    assert world.get_time() == 0
    humans = {entity for entity in world.get_entities() if type(entity) is world_module.Human}
    assert len(humans) == 2
    assert {tuple(human.get_pos()) for human in humans} == {(2, 3)}
    assert world.get_at([2, 3]).get_entities() == humans


def test_random_pos_stays_inside_requested_entity_bounds(monkeypatch):
    world = make_world(width=8, height=7)
    rng = random.Random(4)
    monkeypatch.setattr(world_module.random, "randint", rng.randint)

    positions = [world.random_pos([2, 3]) for _ in range(100)]

    assert all(
        world.valid_pos(x, y)
        and world.valid_pos(x + 1, y + 2)
        for x, y in positions
    )


def test_valid_pos_includes_grid_edges_but_rejects_outside_coordinates():
    world = make_world(width=6, height=7)

    assert world.valid_pos(0, 0)
    assert world.valid_pos(5, 6)
    assert not world.valid_pos(-1, 0)
    assert not world.valid_pos(0, -1)
    assert not world.valid_pos(6, 6)
    assert not world.valid_pos(5, 7)


def test_get_adjacent_nodes_returns_eight_neighbors_and_clips_at_edges():
    world = make_world()

    assert positions(world.get_adjacent_nodes([3, 3])) == {
        (2, 2), (2, 3), (2, 4), (3, 2), (3, 4), (4, 2), (4, 3), (4, 4),
    }
    assert positions(world.get_adjacent_nodes([0, 0])) == {(0, 1), (1, 0), (1, 1)}


def test_find_first_neighbor_searches_adjacent_grid_nodes():
    world = make_world(width=5, height=5)
    start = world.get_at([2, 2])

    found = world.find_first_neighbor(
        start,
        lambda node, target: node.get_pos() == target,
        [3, 2],
    )

    assert found is world.get_at([3, 2])
    assert world.find_first_neighbor(start, lambda node, _: False, None) is None


def test_get_at_maps_xy_to_row_major_storage():
    world = make_world(width=6, height=7)

    assert world.get_at([4, 1]) is world._world[1][4]
    assert world.get_at([4, 1]).get_pos() == [4, 1]


def test_get_nodes_within_uses_euclidean_distance_and_clips_to_grid():
    world = make_world(width=6, height=7)

    assert positions(world.get_nodes_within([3, 3], 1)) == {
        (3, 3), (2, 3), (4, 3), (3, 2), (3, 4),
    }
    assert positions(world.get_nodes_within([0, 0], 1)) == {(0, 0), (1, 0), (0, 1)}
    assert positions(world.get_nodes_within([5, 6], 0)) == {(5, 6)}


def test_nothing_here_detects_occupied_cells_and_ignores_humans():
    world = make_world()
    blocker = MovingEntity([2, 2])
    world.get_at([2, 2]).append(blocker)

    assert not world.nothing_here(MovingEntity([2, 2]), [1, 1])

    world.get_at([2, 2]).remove(blocker)
    human = world_module.Human(world, [2, 2], "A", Race("Blue", (0, 0, 255)))
    world.get_at([2, 2]).append(human)
    assert world.nothing_here(MovingEntity([2, 2]), [1, 1])


def test_nothing_here_checks_cells_on_world_edges_and_rejects_out_of_bounds():
    world = make_world(width=6, height=7)
    blocker = MovingEntity([5, 6])
    world.get_at([5, 6]).append(blocker)

    empty_world = make_world(width=6, height=7)
    assert empty_world.nothing_here(MovingEntity([5, 6]), [1, 1])
    assert empty_world.nothing_here(MovingEntity([4, 5]), [2, 2])
    assert not empty_world.nothing_here(MovingEntity([6, 6]), [1, 1])

    world = make_world(width=6, height=7)
    blocker = MovingEntity([5, 6])
    world.get_at([5, 6]).append(blocker)
    assert not world.nothing_here(MovingEntity([5, 6]), [1, 1])
    assert not world.nothing_here(MovingEntity([4, 5]), [2, 2])


def test_put_entity_registers_all_occupied_cells_for_its_dimensions():
    world = make_world()
    entity = MovingEntity([1, 2], dim=[2, 3])

    world.put_entity(entity)

    expected = {(x, y) for x in (1, 2) for y in (2, 3, 4)}
    assert entity in world.get_entities()
    assert all(entity in world.get_at([x, y]).get_entities() for x, y in expected)
    assert sum(entity in square.get_entities() for row in world._world for square in row) == 6


def test_put_entity_moves_overlap_to_nearest_available_neighbor():
    world = make_world()
    blocker = MovingEntity([2, 2])
    world.get_at([2, 2]).append(blocker)
    world.get_entities().add(blocker)
    entity = MovingEntity([2, 2])

    world.put_entity(entity)

    x, y = entity.get_pos()
    assert max(abs(x - 2), abs(y - 2)) == 1
    assert entity in world.get_at([x, y]).get_entities()
    assert entity not in world.get_at([2, 2]).get_entities()
    assert entity in world.get_entities()


def test_do_tick_updates_entity_occupancy_after_movement():
    world = make_world()
    entity = MovingEntity([1, 1], next_pos=[2, 3])
    world.get_at([1, 1]).append(entity)

    world.do_tick(entity)

    assert entity.tick_count == 1
    assert entity not in world.get_at([1, 1]).get_entities()
    assert entity in world.get_at([2, 3]).get_entities()


def test_tick_advances_time_and_updates_every_entity():
    world = make_world()
    first = MovingEntity([0, 0], next_pos=[1, 0])
    second = MovingEntity([5, 6], next_pos=[4, 6])
    for entity in (first, second):
        world.get_entities().add(entity)
        world.get_at(entity.get_pos()).append(entity)

    world.tick()

    assert world.get_time() == 1
    assert first.tick_count == second.tick_count == 1
    assert first in world.get_at([1, 0]).get_entities()
    assert second in world.get_at([4, 6]).get_entities()


def test_world_dimension_and_entity_accessors():
    world = make_world(width=6, height=7)
    entity = MovingEntity([2, 3])
    world.get_entities().add(entity)

    assert world.get_dim() == [6, 7]
    assert world.get_world_dim() == [6, 7]
    assert world.get_max_dim() == 5
    assert world.get_random_entity() is entity
