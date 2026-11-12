default:
    @just --list

setup:
    uv sync --locked

run *ARGS:
    uv run --locked main.py {{ ARGS }}

test:
    uv run --locked pytest

lint:
    uv run --locked ruff check .

format:
    uv run --locked ruff format .

check: lint test

lock:
    uv lock
