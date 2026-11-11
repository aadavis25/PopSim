PopSim
======

A fishtank-style population simulation about humans living and interacting in four tribes.

Game philosophy
--------------

See [docs/game-philosophy.md](docs/game-philosophy.md) for the game’s design principles, tick and energy model, human decision loop, and current prototype behavior.

Setup and run
-------------

Run `./setup.sh`, then launch with the virtual environment's Python:

- Unix: `./venv/bin/python main.py`
- Windows Git Bash: `./venv/Scripts/python.exe main.py`

Optional arguments: `-w`/`--width`, `--height`, and `-p`/`--population`. All values must be positive integers.

Tests
-----

Run pytest from the virtual environment:

- Unix: `./venv/bin/pytest`
- Windows Git Bash: `./venv/Scripts/pytest.exe`
