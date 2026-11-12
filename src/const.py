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
NANOSECONDS_PER_SECOND = 1_000_000_000
tick_speed_ns = NANOSECONDS_PER_SECOND / 60

# dim
house_dim = [4, 4]
obelysk_dim = [10, 10]
food_dim = [2, 2]
human_dim = [2, 2]

# Race imports Obelysk, which needs the dimensions above.
from src.race import Race

# world
TITLE = "Grid"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 900
TILE_SIZE = 100
PEOPLE = 200
FOOD_NODES = int(WINDOW_WIDTH / 100 * WINDOW_HEIGHT / 100)


def len_minus_one(arr):
    return len(arr) - 1


races = [
    Race("Blue", (0, 0, 255)),
    Race("Red", (255, 0, 0)),
    Race("Yellow", (255, 255, 0)),
    Race("Pearl", (192, 192, 192)),
]
max_target_ticks = 300
