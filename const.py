import math
from collections import deque

import race

# constants
genders = ['M', 'F']
personalities = ['A', 'a', 'B', 'b']
races = [race.Race('Blue', (0, 0, 255)), race.Race('Red', (255, 0, 0)),
         race.Race('Green', (0, 128, 0)), race.Race('Pearl', (192, 192, 192))]
interact_dist = 3
see_dist = 25
marry_chance = 20
marry_gender = genders[0]
max_energy = 9000
house_dim = [4, 4]
obelysk_dim = [10, 10]
want_to_see_ticks = 18000
max_call = 45000
max_interactions_per_tick = 1
tick_speed_ns = 33333333.33


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
