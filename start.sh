#! /usr/bin/env bash
set -e


# # Run migrations
# alembic upgrade head

# alembic revision --autogenerate -m 'create db'
# Run migrations
alembic upgrade head

# Let the DB start
python backend_pre_start.py
# Create initial data in DB
python initial_data.py
# python pre_start.py
gunicorn --reload -c gunicorn_conf.py