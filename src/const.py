import math
from collections import deque

# humans
genders = ['M', 'F']
personalities = ['A', 'a', 'B', 'b']
interact_dist = 2
see_dist = 10
marry_chance = 20
friend_chance = 2
marry_gender = genders[0]
max_energy = 9000
want_to_see_ticks = 18000
interaction_delay = 150
max_call = 45000
max_interactions_per_tick = 1
talking_to_max = 9

# system
tick_speed_ns = 33333333.33
ONE_MILLION = 1000000000

# dim
house_dim = [4, 4]
obelysk_dim = [10, 10]
food_dim = [2, 2]
human_dim = [2, 2]

# world
TITLE = "Grid"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 900
TILES_HORIZONTAL = int(WINDOW_WIDTH / 10)
TILES_VERTICAL = int(WINDOW_HEIGHT / 10)
TILE_SIZE = 100
PEOPLE = 200
FOOD_NODES = int(WINDOW_WIDTH / 100 * WINDOW_HEIGHT / 100)


def len_minus_one(arr):
    return len(arr) - 1


def find_first_neighbor(start_node, func, args):
    visited = set()
    queue = deque()
    visited.add(start_node)
    queue.append(start_node)
    while queue:
        m = queue.popleft()
        for neighbor in m.get_neighbors():
            if neighbor not in visited:
                if func(neighbor, args):
                    return neighbor
                visited.add(neighbor)
                queue.append(neighbor)
    return None


def get_all_nodes_within(start_node, dist):
    visited = set()
    queue = deque()
    queue.append(start_node)
    while queue:
        m = queue.popleft()
        for neighbor in m.get_neighbors():
            if math.dist(start_node.get_pos(), neighbor.get_pos()) <= dist and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited
