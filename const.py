import math

import race

# constants
genders = ['M', 'F']
personalities = ['A', 'a', 'B', 'b']
races = [race.Race('Blue', (0, 0, 255)), race.Race('Red', (255, 0, 0)),
         race.Race('Green', (0, 128, 0)), race.Race('Pearl', (192, 192, 192))]
interact_dist = 2
see_dist = 10
marry_chance = 10
marry_gender = genders[0]
max_energy = 100
house_dim = [5, 5]
want_to_see_ticks = 600
max_call = 1800
max_interactions_per_tick = 1


def len_minus_one(arr):
    return len(arr) - 1


def how_far(pos1, pos2):
    return math.dist(pos1, pos2)
