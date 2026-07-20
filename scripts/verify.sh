#!/usr/bin/env sh
set -eu
python -m compileall src skills
pytest
