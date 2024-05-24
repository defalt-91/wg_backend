#! /usr/bin/env bash
set -e
set -x

export PYTHONBUFFERED=1
export PYTHONWRITEBYTECODE=1
export PORT=8000
export HOST=0.0.0.0
export umask=077
# # Run migrations
# alembic upgrade head
# alembic revision --autogenerate -m 'create db'
# Run migrations
# alembic upgrade head
# ip link add dev wg0 type wireguard
# Let the DB start
python backend_pre_start.py
# Create initial data in DB
python initial_data.py
# python pre_start.py
.venv/bin/gunicorn -c gunicorn_conf.py
#APP_MODULE=
#WORKER_CLASS=
#GUNICORN_CONF=
#exec gunicorn -k "$WORKER_CLASS" -c "$GUNICORN_CONF" "$APP_MODULE"










