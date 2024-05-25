#! /usr/bin/env bash
set -e
set -x

export PYTHONBUFFERED=1
export PYTHONWRITEBYTECODE=1
export DEBUG=True
#export umask=077
#alembic upgrade head
python backend_pre_start.py
python initial_data.py
.venv/bin/uvicorn wg_backend.main:app --reload --port 8000 --host 0.0.0.0


