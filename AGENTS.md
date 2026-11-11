# Repository instructions

## Project

PopSim is a Python population simulator with a Pygame grid display. The application entry point is `main.py`; simulation entities and world behavior live under `src/`.

## Setup and running

- Dependencies are listed in `requirements.txt`: pygame below Python 3.14, or the pygame-ce drop-in package on Python 3.14+.
- `setup.sh` creates a local `venv` and installs dependencies on Unix-like systems and Git Bash on Windows.
- Launch with the virtual environment interpreter: `./venv/bin/python main.py` on Unix or `./venv/Scripts/python.exe main.py` in Windows Git Bash. Optional integer arguments: `-w` width, `-i` height, `-p` population.

## Code conventions

- Keep simulation behavior in the existing `src/` modules and the Pygame application loop in `main.py`.
- Reuse existing constants and model types from `src/`; avoid duplicating simulation configuration.
- Preserve the current Python module/import layout (`src.*`). Keep changes focused and consistent with nearby code.

## Verification

- Run tests with pytest (see README). For changes affecting runtime behavior, also run the application or a focused Python check; graphical changes require checking the Pygame window.
- Do not commit the local virtual environment created by `setup.sh`.
