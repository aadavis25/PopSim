PopSim
======

A fishtank-style population simulation about humans living and interacting in four tribes.

Game philosophy
--------------

See [docs/game-philosophy.md](docs/game-philosophy.md) for the game’s design principles, tick and energy model, human decision loop, and current prototype behavior.

Setup and run
-------------

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and [just](https://github.com/casey/just#installation), then run `just setup` from the project root. Launch with `just run`; pass application arguments after the recipe, quoting options that begin with `-`, for example `just run '--width' 80`.

Recipes:

- `just setup`: sync dependencies from `uv.lock`
- `just run`: launch PopSim
- `just test`: run pytest
- `just lint`: run Ruff checks
- `just check`: run lint and tests
- `just format`: format Python files
- `just lock`: update `uv.lock`
