#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

source .venv/bin/activate
PYTHONPATH=src python -m photo_tagger.app
