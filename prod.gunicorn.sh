#! /usr/bin/env bash
set -e
set -x

#export PYTHONBUFFERED=1
#export PYTHONWRITEBYTECODE=1
#export PORT=8000
#export HOST=0.0.0.0
#export umask=0o700
export DEBUG=False
python backend_pre_start.py
# Create initial data in DB
python initial_data.py

exec .venv/bin/gunicorn -c gunicorn_conf.py










