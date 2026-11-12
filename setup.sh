#!/bin/bash -e

if ! command -v uv >/dev/null 2>&1; then
    printf 'uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/.\n' >&2
    exit 1
fi

uv sync --locked
