#!/bin/bash -e

if command -v python3 >/dev/null 2>&1; then
    python_executable=python3
elif command -v python >/dev/null 2>&1; then
    python_executable=python
else
    printf 'Python 3 is required to create the virtual environment.\n' >&2
    exit 1
fi

"$python_executable" -m venv ./venv

if [ -f ./venv/bin/python ]; then
    venv_python=./venv/bin/python
elif [ -f ./venv/Scripts/python.exe ]; then
    venv_python=./venv/Scripts/python.exe
else
    printf 'Could not locate the virtual environment Python executable.\n' >&2
    exit 1
fi

"$venv_python" -m pip install wheel
"$venv_python" -m pip install -r requirements.txt
