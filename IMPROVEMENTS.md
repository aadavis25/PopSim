# PopSim: Improvements, Test Plan, and Gaps

Review of the working tree at the time of the original review. Human findings and their test cases were checked against current source; other findings retain the original review status.

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
| B1 | `Human.stop_talking` | Calling `stop_talking()` without a partner previously dereferenced `None`. | **Fixed:** checks `talking_to[0]` before clearing the partner; the at-home recovery test exercises this path. |
| B2 | `Human.nap`, `Human.do_something` | Napping could stall because energy drained while napping and no code continued the recovery. | **Fixed:** depleted humans nap at home, recover by 5 energy per tick, and wake at `max_energy`; the full recovery test covers this path. |
| B3 | `Human._target`, `Human.talking_to` | Targets and conversation state previously mixed tuple and list forms. | **Fixed:** both are consistently initialized and assigned as lists. |
| B4 | `Human.look_around`, `Human.interact`, `Human.walkabout` | **Fixed:** visibility sets exclude `self`; nearby interaction rejects self; wandering excludes self from random candidates. |
| B5 | `World` state used by Humans | **Partially fixed:** `_entities_to_add` is per-instance, but `_world_dim`, `_entities`, and module-level race/obelisk state remain shared. Move mutable world and race state to each `World` instance. |
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
| R1 | `Human.interact` | Busy humans could be targeted for conversation. **Fixed:** interaction rejects talking, napping, and call-expired targets without changing their state. |
| R2 | `Human.get_married`, `Human.interact` | Previously only the initiating human's spouse was checked. **Fixed:** marriage now requires both humans to be unmarried. |
| R3 | `Human.get_married`, `Human.build_house` | `get_married()` only sets spouse links; `build_house()` has no callers. Marriage currently creates no shared house, and repeated direct calls could create orphans. **Open:** connect marriage to one-time shared-house creation and test world registration. |
| R4 | Human resource behavior | No resource pickup/deposit logic currently exists in `Human`; the previously reported unconditional pickup is not present. **Deferred** until resource-driven construction is implemented. |
| R5 | Human resource behavior | No carry/build threshold logic currently exists in `Human`. **Deferred** until resource-driven construction is implemented. |
| R6 | Human resource behavior | No resource-target selection currently exists in `Human`. **Deferred** until that activity is implemented. |
| R7 | `Human.can_be_friends`, `Human.interact` | Friendship eligibility was bypassed, and its chance check used `is`. **Fixed:** conversation completion calls `can_be_friends()` and its integer comparison uses `==`. |
| R9 | `Human.do_something` | At zero energy, a human without a house could previously receive a `None` target. **Fixed:** exhausted humans target their home, or their own obelisk when houseless. |
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
- **Fixed:** `look_around()` reuses its visibility/nearby sets; `World.get_random_entity()` caches choices instead of copying the entity set per wander, and wandering excludes self.
- **Fixed:** Human memories use entity-keyed lookup instead of scanning a set; duplicate memory updates preserve the existing `Memory` object.
- **Fixed:** `world_loop` waits for the remaining 1/60-second tick interval when early and warns only when a tick exceeds it.

Optional (**ask first**, it changes the world representation):
- Current grid storage is still a dense two-dimensional list; replacing it with `dict[(x, y)] → set[Entity]` remains an optional redesign if profiling justifies it.
- **Fixed:** `World.get_nodes_within()` lazily caches the offset list for each queried distance.
- The former KDTree, path-map, and JSON-cache designs are absent from current source; only the dense-grid representation remains under consideration.

---

## 3. Structure and maintainability

- **Make `World` testable**: accept `path_map` (or `None`) and an `rng: random.Random` rather than calling module-level `random`. Seedable runs also allow determinism tests and a `--seed` flag.
- **Fixed:** neither `human.py` nor `main.py` prints progress messages.
- **Remove dead code** (each name has no callers except its own definition):
  - `len_minus_one`, `get_all_nodes_within` (`const.py`)
  - `get_max_dim`, `get_world_dim` (`world.py`)
  - `Entity.set_nearby`, `Human.set_can_see`
  - unused constants `max_interactions_per_tick`, `max_hunger`
  - commented blocks in `human.py` (timing, hunger, friend-summon) and `world.py:64, 103-104`
- **Constants**: mixed `snake_case` and `UPPER_CASE` in `const.py`. Typo "rezourses". `FOOD_NODES` now builds `ResourceNode`s.
- **Types:** the tuple/list mismatch from B3 is fixed, but `set_target(List[Entity | int])` still models a heterogeneous target and could use a target type.
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

`test/human.py` is obsolete. **Fixed:** Human tests now live in `tests/test_human.py`, use `src.*` imports, and do not construct a `World` at import time.

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
| M4 | Repeated `move_toward` | Reaches the target in `max(|dx|, |dy|)` movement steps; at the default cadence that takes two ticks per step. |
| M5 | Many steps from random positions | Never leaves the world. |
| M6 | Target initialized through `clear_target()` | Movement accepts the initial target without a tuple/list `TypeError`. **Fixed (B3).** |

**Talking and relationships**

| ID | Case | Expected |
|---|---|---|
| K1 | `stop_and_talk` | Both humans point at each other with `talking_to_max`. **Fixed:** the method assigns both links. |
| K2 | `stop_talking` with no partner | No-op. **Fixed (B1):** the no-partner case is guarded. |
| K3 | `stop_talking` with a partner | Clears both sides. **Fixed:** the method clears the partner and local link. |
| K4 | A human never selects itself (nearby or `walkabout`) | **Fixed (B4).** |
| K5 | Explicitly targeting a napping, calling, or talking human | that human's state is not overwritten. **Fixed (R1).** |
| K6 | Conversation timing | Memory is recorded after the countdown; verify the intended `talking_to_max` boundary and symmetric acquaintance update. **Needs verification.** |
| K7 | Friendship eligibility | `add_friend` runs only when `can_be_friends()` returns true. **Fixed (R7).** |
| K8 | Marriage requires: friends, same personality, same race, different genders, `self` is `marry_gender`, **both** unmarried, roll hit | implementation checks these eligibility rules; full condition-matrix regression coverage remains open. |
| K9 | Already-married `other` | not re-married. **Fixed (R2).** |
| K10 | Marriage | spouses symmetric; both reference the same house; house is in the world; the previous houses are not left orphaned. **Open (R3; house-building deferred).** |
| K11 | `want_to_talk` boundary | `interaction_delay` ticks ago is rejected and `+1` accepted; interaction rejects talking, napping, and call-expired targets. **Busy-target behavior fixed (R1); delay-boundary test remains unverified.** |
| K12 | `add_memory` twice | one memory, time updated. **Fixed:** tested. |
| K13 | `remember` an unknown entity | `None`. **Fixed:** tested. |

**Energy, napping, call**

| ID | Case | Expected |
|---|---|---|
| N1 | Energy | Movement and idle ticks do not drain energy; an active conversation tick costs 1. **Fixed:** covered by Human behavior tests. |
| N2 | At 0 energy | Targets the home, or the human's own obelisk if houseless. **Fixed:** covered by Human behavior tests. |
| N3 | Nap | Energy rises and the human wakes at `max_energy`. **Fixed:** full home-rest recovery is tested. |
| N4 | After waking | `get_napping()` is false and normal goal selection resumes. **Fixed:** full home-rest recovery is tested. |
| N5 | Energy cap | Energy never exceeds `max_energy`, including when recovery overshoots. **Fixed:** `nap()` clamps the increase and wakes at the cap. |
| C1 | `_the_call` | Decrements, and `calling()` flips at 0. **Implemented:** `tick()` decrements the counter and `calling()` checks for zero. |
| C2 | At call 0 during a conversation | A call-expired human should stop talking and target its own obelisk. **Partially fixed:** `stop_talking()` is safe, but `do_something()` returns while talking and does not interrupt the conversation. |
| C3 | Touching an obelisk | Own obelisk resets `_the_call`; another race's does not. **Implemented:** `interact()` checks obelisk identity. |

**Houses and resources**

| ID | Case | Expected |
|---|---|---|
| H1 | Marriage and house-building | Marriage should create one shared house at the tribe obelisk. **Open (R3):** `build_house()` has no caller. |
| H2 | Resource pickup | No resource pickup activity is implemented; defer this case until resource activities exist. |
| H3 | Pickup when house is built or absent | No resource pickup activity is implemented; defer this case until resource activities exist. |
| H4 | Deposit | No resource deposit activity is implemented; defer this case until resource activities exist. |
| H5 | `HOUSE_BUILT_RESOURCE / RESOURCE_MAX_CARRY` deposits | No resource construction activity is implemented; defer this case until resource activities exist. |
| H6 | Carry overshoot | No resource construction activity is implemented; defer this case until resource activities exist. |
| H7 | Several resource nodes visible | No resource target selection is implemented; defer this case until that activity exists. |
| H8 | Target not reached after `max_target_ticks` | Cleared, unless obelisk or house. **Implemented:** `do_something()` applies the configured timeout. |

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

1. Finish conversation/call behavior (C2), then verify conversation timing and the marriage eligibility matrix (K6/K8).
2. Move mutable `World` state to each instance (B5), then reassess remaining world findings against the current grid implementation.
3. Keep regression tests in `tests/`; add focused coverage for each remaining behavior before fixing it.
4. Reassess historical World/cache findings against current source before treating them as active work.
5. Keep threading and shutdown (R10, R11), rendering (R15), and tick timing marked fixed unless a regression appears.
6. Consider a grid representation change only after profiling; the old KDTree/path-map/JSON-cache proposal is obsolete.
7. Update remaining README, requirements, and dead-code findings only if they still apply to the current tree.
