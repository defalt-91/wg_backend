#! /usr/bin/env bash
set -e
DEFAULT_GUNICORN_CONF=/app/gunicorn_conf.py

# # Run migrations
# alembic upgrade head
# alembic revision --autogenerate -m 'create db'
# Run migrations
alembic upgrade head
# ip link add dev wg0 type wireguard
# Let the DB start
python backend_pre_start.py
# Create initial data in DB
python initial_data.py
# python pre_start.py
gunicorn -c gunicorn_conf.py
# exec gunicorn -k "$WORKER_CLASS" -c "$GUNICORN_CONF" "$APP_MODULE"