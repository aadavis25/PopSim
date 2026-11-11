# PopSim: Improvements, Test Plan, and Gaps

Review of the working tree at the time of the original review (not HEAD). Main-loop findings marked **Fixed** were addressed in the follow-up refactor; other findings remain open.

**Evidence levels**
- **Reproduced**: I ran a throwaway script against the code (in a temp directory so `cfg/path_map.json` was not touched).
- **Read**: found by reading the code, not run.
- **Inferred**: extrapolation. The reasoning is stated.

Findings are ordered by severity. Fixes are the smallest ones I can see. Anything that changes architecture or adds a dependency is marked **ask first**.

---

## 1. Bugs

### 1.1 Reproduced

| # | Where | Problem | Fix |
|---|---|---|---|
| B1 | `human.py:247-250` `stop_talking` | `if self._talking_to:` is always true because `_talking_to` is a non-empty tuple `(None, 0)`. With no partner it calls `None.clear_talking_to()` and raises `AttributeError`. It runs from `nap()` and, every tick once `_the_call` reaches 0 (45 000 ticks ≈ 12.5 min at 60 Hz), from `find_target`. The exception kills the world thread (see B12), so the window keeps drawing a frozen world. | `partner = self.get_talking_target()`; `if partner: partner.clear_talking_to()`; `self.clear_talking_to()`. |
| B2 | `human.py:73-74, 199-206` | `interact()` returns early while `_napping`, but `nap()` is only called from `interact()`. After the first nap, energy is 5, decays to 0, and the human stays napping forever (`is_busy()` stays true). Reproduced: after 2000 ticks, `napping=True`, `energy=0`. In a full run B1 usually fires first, unless the human happens to be talking. | Move wake-up logic into `tick`/`decrement`: while napping, add energy and clear `_napping` at `>= max_energy`. Use `>=`, not `==`. |
| B3 | `human.py:38, 265-266, 146` | `_target` is sometimes a tuple (`__init__`, `clear_target`) and sometimes a list (`set_target` callers). `move()` does `self._target[1] += 1`, which raises `TypeError` on a tuple. This is reached whenever a Human is built while its race already has an obelysk, i.e. the second `World` in a process (B5). Same tuple/list mix exists for `_talking_to`. | Store `_target` and `_target_age` as separate fields. |
| B4 | `human.py:79-86`, `world.py:162` | `_nearby` includes the human itself (its own square is in `interact_from_here`) and `get_random_entity()` can return the human. `interact()` then calls `stop_and_talk(self)`. Reproduced: `_talking_to[0] is self`. The human talks to itself, runs `add_known(self)`, and wastes 9 ticks. | `self._nearby.discard(self)` in `look_around`. Exclude `self` in `walkabout`. |
| B5 | `world.py:44-49, 18-19` | `_world_dim`, `_entities`, and `_entities_to_add` are class attributes, and `__init__` mutates them in place. `races` is a module global holding obelysk state. A second `World` inherits the first's entities and obelysks. Reproduced: two 5-human worlds gave 10 entities in the second, and `w1._entities is w2._entities` was `True`. This is the main obstacle to isolated tests. | Move to `__init__`. Build `races` inside `World.__init__` or via a `make_races()` helper. |
| B6 | `world.py:111-119` `put_house` | `randint` upper bound is `_world_dim` (one past the last index), and a 4×4 house also overhangs the edge. Reproduced: `IndexError` in 355/2000 calls on a 40×40 world. At 900×900 the chance per call is lower but non-zero [inferred]. | Clamp the range to `[0, dim - house_dim - 1]`. |
| B7 | `world.py:134-142` `nothing_here` | Returns `True` (free) when the footprint is out of bounds, because the check is skipped. `valid_pos(x + dim, y + dim)` treats the exclusive end as an inclusive index, so an entity that exactly fits against the far edge is never collision-checked. Reproduced: a House at `[38,38]` on 40×40 over a ResourceNode returned `True`. `put_entity` then raises `IndexError` while registering squares. | Check the last occupied cell `(x + dim - 1, y + dim - 1)`. Return `False` when out of bounds. |
| B8 | `world.py:22-40` `encode_poss`/`decode_poss` | Encodes only min and max x per row, so rows with gaps are not preserved. `neighbors` of `(x, y)` contains `x-1` and `x+1` but not `x`, so decoding adds the node itself. Reproduced: `[[1,1],[3,1],[2,2]]` came back with an extra `[2,1]`. Neighbors from the cache therefore differ from a fresh build. | Store the `neighbors` row as the explicit list. Keep range encoding for `see` and `interact`, which are convex discs. |
| B9 | `world.py:176-220`, `cfg/` | See below. | See below. |

**B9 path-map cache.**
- `cfg/path_map.json` has 249 999 lines, so it is a 500×500 map. The default window is 900×900 (`const.py:32-33`), so the default run never hits the cache. It rebuilds and **overwrites the 123 MB file**. Any `World(10, 10, 0)` does the same, including the existing test.
- Validity is checked only by entry count. Changing `see_dist`/`interact_dist`, or using a different W×H with the same product, loads a wrong map silently.
- The path is relative to the cwd. The file handle is never closed.
- `cfg/` and `out/` are untracked and not in `.gitignore`, so a 123 MB file can be committed by accident.

Fix options:
- Smallest: key the cache file by `(w, h, see_dist, interact_dist)` and anchor it to `Path(__file__)`. Add `cfg/` and `out/` to `.gitignore`.
- Better (**ask first**): see §3. Drop the cache entirely.

### 1.2 Read, not reproduced

| # | Where | Problem |
|---|---|---|
| R1 | `human.py:79-80, 88-89` | When the target is in `_nearby`, `want_to_interact`/`is_busy` are bypassed. `stop_and_talk` can overwrite a napping, calling, or already-talking partner and leave a third party with a dangling `_talking_to`. |
| R2 | `human.py:118-123, 125-131` | `get_married` checks only `self._spouse`, not `other`'s. A married `other` gets a new spouse and house, and the old spouse still points at them. |
| R3 | `human.py:125-131, 170-171` | Marriage creates a second house. The first one (from `put_house` in `find_target`) stays in the world forever; there is no `remove_entity`. `House._owner` is never read. |
| R4 | `human.py:93-96` | Resource pickup is unconditional: it happens even with no house, or when the house is built. Nodes are never depleted. `print("getting resource")` printed about 190 times in 150 ticks with 200 humans. |
| R5 | `human.py:103` | `== HOUSE_BUILT_RESOURCE` breaks if the carry amount or target changes. Use `>=`. |
| R6 | `human.py:174-176` | Resource choice is "last one seen in set iteration order", not the nearest. It is non-deterministic across runs. |
| R7 | `human.py:226`, `human.py:116-122` | `random.randint(...) is marry_chance` compares ints by identity. It works only because CPython caches small ints. `can_be_friends` is never called, so the personality/race rule for friendship does nothing; friendship is a bare coin flip. |
| R9 | `human.py:162-163` | At zero energy, `set_target([self._house, 0])` is set even when `_house` is `None`. |
| R10 | `main.py:62-89` | Iterates `the_world.get_entities()` on the main thread while the world thread's `tick()` calls `_entities.update(...)`. This can raise `RuntimeError: Set changed size during iteration`. There is no lock. **Fixed:** world ticks and render snapshots now share a lock. |
| R11 | `main.py:26-31, 91-96` | The world thread is non-daemon. If the render loop raises, nothing sets the stop event and the process hangs. An exception in the world thread is not logged or propagated. **Fixed:** shutdown sets the stop event and joins the thread; worker exceptions are logged and re-raised. |
| R12 | `world.py:101-109` | `do_tick`→`update` runs `remove` then `append` on every entity every tick, including static ones. For multi-tile entities only the origin square is touched, which works by accident. |
| R13 | `world.py:204-220` | Only `FileNotFoundError` and `JSONDecodeError` are caught. A wrong-schema or out-of-range cache raises `KeyError`/`TypeError`/`IndexError` at startup. |
| R14 | `const.py:22` | `ONE_MILLION = 1000000000` is one billion. The sleep is correct (seconds) but the name is wrong, and the `waiting:` print is in seconds, not ms. **Fixed:** renamed the unit constant and removed the slack-time print; overruns are logged in milliseconds. |
| R15 | `main.py:45-61` | `TILE_SIZE = 100` with 90×90 tiles issues 8 100 `draw.rect` calls per frame, almost all off-screen on a 900 px window. `row` and `col` are swapped. Tile counts ignore `-w`/`-i`. `self.clock` is created but never ticked, so the loop is uncapped. **Fixed:** renderer caches correctly bounded tiles for the configured dimensions, uses x/y positions consistently, and caps frames at 60 FPS. |
| R16 | `entity.py`/`house.py` | `House._dim = const.house_dim` aliases a module-level list. Mutating one house's dim changes all. Use tuples. |
| R17 | `human.py`, `world.py`, `main.py` | Exact `type(x) is …` checks appear 13 times across the three files. Subclasses silently fail every check. Prefer `isinstance`. |

---

## 2. Performance

Measured: 300×300 world, 200 humans, from-scratch build, 150 ticks.

| Metric | Result |
|---|---|
| World build (no cache) | 9.6 s |
| Tick median / p95 | 6.3 ms / 8.5 ms (budget at 60 Hz: 16.7 ms) |
| Peak RSS | about 0.62 GB |
| Cache file | 45 MB |

- Memory and build time scale with W×H: 900×900 is 9× the squares. Linear extrapolation gives about 5.6 GB and about 90 s [inferred]. Every `WorldSquare` stores three collections (about 8 neighbors, about 13 interact squares, about 317 see squares).
- Per tick, `look_around` builds two sets from about 330 squares for each human.
- `walkabout` calls `list(self._entities)` on every call.
- `remember`/`add_memory` scan a set linearly. Use `dict[entity, tick]`.
- **Fixed:** `world_loop` waits for the remaining 1/60-second tick interval when early and warns only when a tick exceeds it.

Optional (**ask first**, it changes the world representation):
- Replace the 810k-square grid, the KDTree, and the JSON cache with a `dict[(x, y)] → set[Entity]`.
- Precompute the offset lists once (about 317 `(dx, dy)` pairs for see, about 13 for interact).
- This removes `cfg/path_map.json` and `scipy`, and fixes B8/B9 and the startup cost.
- It also makes `World` trivially constructible in tests.

---

## 3. Structure and maintainability

- **Make `World` testable**: accept `path_map` (or `None`) and an `rng: random.Random` rather than calling module-level `random`. Seedable runs also allow determinism tests and a `--seed` flag.
- **Replace `print`** in `human.py` (`"napping"`, `"getting resource"`) and `main.py` with `logging`, off by default.
- **Remove dead code** (each name has no callers except its own definition):
  - `len_minus_one`, `get_all_nodes_within` (`const.py`)
  - `get_max_dim`, `get_world_dim` (`world.py`)
  - `Entity.set_nearby`, `Human.set_can_see`, `get_energy`, `can_be_friends`, `summon`
  - unused constants `want_to_see_ticks`, `max_interactions_per_tick`, `max_hunger`
  - commented blocks in `human.py` (timing, hunger, friend-summon, memory-seek) and `world.py:64, 103-104`
- **Constants**: mixed `snake_case` and `UPPER_CASE` in `const.py`. Typo "rezourses". `FOOD_NODES` now builds `ResourceNode`s.
- **Types**: several annotations are wrong (`get_target_object() -> Entity` can be `None`; `set_target(List[Entity | int])` is a heterogeneous list). A target dataclass fixes both and B3.
- **Getters/setters**: some fields are public (`House.resource`, `.built`, `.items`), others use `get_*`. Pick one. Prefer plain attributes, which is idiomatic Python.
- **Rendering (fixed):** entity drawing moved into `GridRenderer`, which caches the checkerboard; `clock.tick(60)` caps frames, and entity dispatch uses `isinstance`.
- **CLI (fixed):** `-i` was replaced by `--height`; width and population have long options, and all supplied values must be positive integers.

---

## 4. Repository hygiene and docs

- `.gitignore`: add `cfg/path_map.json` (or all of `cfg/`) and `out/`. Delete `out/production/` (stale IntelliJ build copy). Root `bin/` and `include/` are venv leftovers (ignored).
- `requirements.txt` is unpinned. The venv has `pygame 2.6.0` and `scipy 1.14.1`. `typing.Self` requires Python ≥ 3.11 (`.python-version` is 3.12.2); document it. `.python-version` is untracked.
- `setup.sh` is fine. It does not install test or dev tools.
- `README.md` is one sentence. Needs: install, run, CLI flags, what the simulation does (races, obelysks, calls, napping, marriage, house building), Python version, the cache behaviour, how to run tests.
- No CI. No linter or formatter config (**ask first** before adding a tool or CI job).
- No `--seed`, no headless run mode, no way to run N ticks without opening a window.

---

## 5. Test plan

### 5.1 Current state

`test/human.py` cannot run, and should be replaced:
- `from world import World` is the wrong import (`src.world`).
- `class TestFindTarget(HumanTest)` is nested inside `HumanTest`'s body, so it raises `NameError` at import.
- Its only assertion is `assertEqual(True, False)`.
- `World(10, 10, 0)` at class level runs at import and **overwrites `cfg/path_map.json`** (B9).
- The directory `test/` shadows the stdlib `test` package, and `human.py` does not match unittest discovery (`test*.py`).

### 5.2 Infrastructure

1. Rename to `tests/`, files named `test_*.py`.
2. `unittest` needs no new dependency. `pytest` gives fixtures and `parametrize` (**ask first**, it adds a dev dependency). The cases below are framework-neutral.
3. Prerequisite seams (small code changes): `World(path_map=None, rng=…)`, per-instance state (B5). Until then, tests must `chdir` into a temp dir and reset `races`.
4. Helper `make_world(w=40, h=40, people=0, seed=0)` and `make_human(world, pos, **kw)`.
5. Pure-logic tests need no pygame display. For `Game` smoke tests set `SDL_VIDEODRIVER=dummy`.
6. Tests marked **(currently fails)** encode a bug above. Write them first, watch them fail, then fix.

### 5.3 Cases

**World encoding (pure)**

| ID | Case | Expected |
|---|---|---|
| E1 | `decode(encode(p))` for one contiguous row | equals `p` |
| E2 | Several rows, contiguous | equals `p` (order-insensitive) |
| E3 | Empty list | `[]` |
| E4 | Row with a gap, e.g. `[[1,1],[3,1]]` | equals `p`. **(currently fails, B8)** |

**WorldSquare / const helpers**

| ID | Case | Expected |
|---|---|---|
| S1 | `append`/`remove` | entity present then absent |
| S2 | `remove` of an absent entity | defined behaviour (currently `KeyError`) |
| S3 | `find_first_neighbor` on a small hand-built graph | returns the BFS-nearest match |
| S4 | No node matches | `None` |
| S5 | Cyclic graph | terminates |
| S6 | Start node matches | not returned (document it) |

**World construction**

| ID | Case | Expected |
|---|---|---|
| W1 | `World(w, h, n)` | `get_dim() == [w, h]`; `n` humans |
| W2 | After first `tick()` | `FOOD_NODES` resource nodes plus one obelysk per race are in `get_entities()`; before it, they are queued |
| W3 | All entities, across many seeds | footprint fully inside `[0,w) × [0,h)` |
| W4 | Every race has an obelysk after construction | true |
| W5 | Two `World`s in one process | independent entity sets and obelysks. **(currently fails, B5)** |
| W6 | Non-square world (e.g. 30×50) | indexing and spawning never raise |
| W7 | World smaller than `obelysk_dim` | clear error, not a bare `randint` `ValueError` |

**Neighbors, visibility, and cache**

| ID | Case | Expected |
|---|---|---|
| P1 | Neighbor counts | corner 3, edge 5, interior 8, and never includes self |
| P2 | `see` and `interact` sets | equal a brute-force `dist <= radius` scan, including the boundary |
| P3 | Cache round-trip | loaded neighbors/see/interact equal a fresh build. **(currently fails, B8)** |
| P4 | Cache for different dims or radii | ignored, and the existing file is not overwritten. **(currently fails, B9)** |
| P5 | Corrupt JSON, missing file, wrong schema | rebuilds without raising (R13) |
| P6 | Running from a different cwd | same behaviour |

**Placement**

| ID | Case | Expected |
|---|---|---|
| L1 | `put_entity` on a free spot | lands at the requested pos; all `dim` squares reference it |
| L2 | `put_entity` on an occupied spot | relocated to the nearest free spot; original pos unchanged for the other entity |
| L3 | Humans on the target tile | do not block placement |
| L4 | Entity that exactly fits against the far edge | accepted. **(currently fails, B7)** |
| L5 | Entity that does not fit | rejected or clamped, never `IndexError`. **(currently fails, B7)** |
| L6 | No free location anywhere | defined error, not `AttributeError` on `None` (`world.py:124`) |
| L7 | `put_house`, 2000 seeds, obelysk at each corner and each edge | 4×4 footprint always in bounds. **(currently fails, B6)** |
| L8 | Collision check is symmetric | A over B is rejected, and B over A is rejected |

**Tick and update**

| ID | Case | Expected |
|---|---|---|
| T1 | `tick()` | `get_time()` increases by 1 |
| T2 | Human moves | removed from the old square, added to the new one |
| T3 | After `tick()`, a static multi-tile entity | still present on all its squares |
| T4 | Entity added during a tick | not ticked until the next tick |
| T5 | Render thread iterates entities while ticks run | no `RuntimeError` (R10) |

**Human movement**

| ID | Case | Expected |
|---|---|---|
| M1 | Target at same pos | no movement |
| M2 | Pure horizontal / vertical / diagonal | one step along that axis (or both) |
| M3 | Shallow ratio (`dx > 2·dy`) and steep ratio | only the dominant axis moves |
| M4 | Repeated `move_toward` | reaches the target in `max(\|dx\|,\|dy\|)` ticks and stays |
| M5 | Many steps from random positions | never leaves the world |
| M6 | `move()` with the initial tuple target | does not raise. **(currently fails, B3)** |

**Talking and relationships**

| ID | Case | Expected |
|---|---|---|
| K1 | `stop_and_talk` | both humans point at each other with `talking_to_max` |
| K2 | `stop_talking` with no partner | no-op. **(currently fails, B1)** |
| K3 | `stop_talking` with a partner | clears both sides |
| K4 | A human never selects itself (nearby or `walkabout`) | **(currently fails, B4)** |
| K5 | Explicitly targeting a napping, calling, or talking human | that human's state is not overwritten. **(currently fails, R1)** |
| K6 | Talk ends after exactly `talking_to_max` ticks | memory recorded; `add_known` is symmetric |
| K7 | Friendship (patch `random` to hit and miss) | `add_friend` only on a hit |
| K8 | Marriage requires: friends, same personality, same race, different genders, `self` is `marry_gender`, **both** unmarried, roll hit | each condition removed in turn prevents marriage |
| K9 | Already-married `other` | not re-married. **(currently fails, R2)** |
| K10 | Marriage | spouses symmetric; both reference the same house; house is in the world; the previous houses are not left orphaned (R3) |
| K11 | `want_to_interact` boundary | `interaction_delay` ticks ago rejected, `+1` accepted; busy `other` rejected |
| K12 | `add_memory` twice | one memory, time updated |
| K13 | `remember` an unknown entity | `None` |

**Energy, napping, call**

| ID | Case | Expected |
|---|---|---|
| N1 | Energy | decrements 1/tick and saturates at 0 |
| N2 | At 0 energy | targets the house (or defined behaviour with no house) |
| N3 | Nap | energy rises and the human wakes at `max_energy`. **(currently fails, B2)** |
| N4 | After waking | `is_busy()` is false and normal behaviour resumes. **(currently fails, B2)** |
| N5 | Energy never exceeds `max_energy` | true |
| C1 | `_the_call` | decrements, and `calling()` flips at 0 |
| C2 | At call 0 | stops talking without error and targets own obelysk. **(currently fails, B1)** |
| C3 | Touching own obelysk | resets `_the_call`; another race's obelysk does not |

**Houses and resources**

| ID | Case | Expected |
|---|---|---|
| H1 | Houseless human | gets a house on its first `find_target` |
| H2 | Pickup | `RESOURCE_MAX_CARRY` only when empty-handed |
| H3 | Pickup when house is built or absent | no pickup. **(currently fails, R4)** |
| H4 | Deposit | house resource increases; carry resets to 0 |
| H5 | `HOUSE_BUILT_RESOURCE / RESOURCE_MAX_CARRY` deposits | `built` is true |
| H6 | Overshoot (carry not a divisor of the goal) | still built (R5) |
| H7 | Several resource nodes visible | nearest chosen. **(currently fails, R6)** |
| H8 | Target not reached after 300 ticks | cleared, unless obelysk or house |

**Entities and constants**

| ID | Case | Expected |
|---|---|---|
| X1 | `Entity` default dim | `[1, 1]` |
| X2 | `House` pos | copied, not aliased to the obelysk's pos |
| X3 | Mutating one house's dim | does not affect others. **(currently fails, R16)** |

**`main.py`**

| ID | Case | Expected |
|---|---|---|
| G1 | CLI args | defaults used when absent; zero, negative, and non-integer values rejected. **Fixed.** |
| G2 | `Game` smoke with `SDL_VIDEODRIVER=dummy`, small world | N frames render; a QUIT event stops the world thread; `join()` returns. **Fixed.** |
| G3 | Exception in the world thread | surfaced (logged, and stops the game). **Fixed.** |
| G4 | Exception in the render loop | stop event set, process exits. **Fixed.** |
| G5 | `world_loop` timing, with an injected clock | waits for the remaining 1/60-second interval if early; no wait at the exact interval; warns only when over budget. **Fixed.** |

**Simulation and property tests** (seeded; patch `max_call`, `max_energy`, `talking_to_max` small so every state is reached quickly)

| ID | Case | Expected |
|---|---|---|
| Z1 | 60×60 world, 50 humans, 20 000 ticks | no exception |
| Z2 | Invariant, checked every N ticks | every human is in bounds and in exactly the square matching its pos |
| Z3 | Invariant | `_talking_to` and spouse links are symmetric |
| Z4 | Invariant | no human is `napping` with `energy >= max_energy` |
| Z5 | Progress | over a window, no human is stuck napping or targeting the same tile without moving (would have caught B2) |
| Z6 | Determinism | same seed → identical state hash after N ticks (needs the `rng` seam) |
| Z7 | Benchmark (report only, not a pass/fail gate) | tick time at 300×300/200 humans vs the 16.7 ms budget |

---

## 6. Suggested order

1. Fix B1, B3, B4 (about 10 lines in `human.py`). These stop the crashes and the self-talk.
2. Fix B5 (class state → instance state) and make `World` take `path_map`/`rng`. This unblocks isolated tests.
3. Replace `test/human.py` with `tests/`; add the tests marked **(currently fails)** first, then fix B2, B6, B7, B8, B9.
4. Fix B9 immediately if you run anything: add `cfg/` to `.gitignore` and stop the default run overwriting the cache.
5. Threading and shutdown (R10, R11). Rendering (R15).
6. Decide on the grid/cache removal (§2). This is the largest win and the largest change.
7. README, pinned requirements, dead-code removal, logging.
