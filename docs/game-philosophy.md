# PopSim Game Philosophy

## Core experience

PopSim is a fishtank-style simulation about humans living and interacting in four tribes. The focus is observing population behavior: humans encounter one another, form relationships, respond to their surroundings, and meet tribe-specific obligations.

The code currently represents tribes as `Race` objects named Blue, Red, Yellow, and Pearl. Each tribe has its own obelisk. The recurring call is a tribe-specific obligation: when a human's call expires, they should return to their own obelisk; reaching it resets the call.

## Time and energy

A `World.tick()` is the unit of simulation time. Durations, waits, and cooldowns belong in ticks, not wall-clock time. The runtime targets 60 ticks per second.

Activities have activity-specific durations and energy costs. Energy should be spent on activities, not passively because ticks pass; rest can restore energy. This is the intended model even where the current implementation has not caught up.

## Human behavior

Preserve the human decision loop:

1. `Human.tick()` observes surroundings through `look_around()`.
2. It handles interactions through `interact()`, using nearby entities and the current target.
3. `do_something()` chooses or advances goals using surroundings and the current target.

Current goals are rigid and simplistic. They include seeking people, responding to the call, seeking a home when energy is depleted and one exists, revisiting friends, and wandering. Extend this behavior incrementally; do not treat today's priorities as the final AI design.

Memory is minimal: a human remembers an entity and the tick of the last interaction. It is a prototype foundation, not a complete account of a human's past.

## Social life and homes

Humans have gender and personality, can interact, form relationships, marry, and share homes. These systems should support observable social behavior without making today's prototype rules permanent design constraints.

Current prototype details:

- Humans are assigned one of two gender values (`M`, `F`) and one of four personality values (`A`, `a`, `B`, `b`).
- A completed conversation records mutual acquaintance. A chance-based rule may add a friendship; the existing `can_be_friends()` method does not currently gate that rule.
- Current marriage attempts require the initiating human to have the other as a friend, the same tribe and personality, and different genders. Only `M`-coded humans initiate marriage.
- Marriage creates a shared house initially positioned at the tribe obelisk. World placement resolves collisions, so the final position can differ.

House-building is an intended activity. The current prototype does not model a separate resource-gathering and construction process; it creates the shared house when humans marry. Do not describe resource-driven construction as implemented until it exists.

## Evolving the simulation

Goals and relationships are expected to grow beyond their current prototype behavior. Prefer clear, incremental changes that preserve the tick-based simulation and human decision loop. Document current behavior separately from design intent; do not overstate unfinished mechanics or turn incidental rules into permanent requirements.
