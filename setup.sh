#!/bin/bash -e

python3 -m venv ./venv

source ./venv/bin/activate

pip install wheel

pip install --upgrade pip
pip install -r requirements.txt
deactivate
