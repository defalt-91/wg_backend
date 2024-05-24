export PYTHONBUFFERED=1
export PYTHONWRITEBYTECODE=1
export PORT=8000
export HOST=0.0.0.0
export umask=077
#alembic upgrade head
python backend_pre_start.py
python initial_data.py
.venv/bin/uvicorn app.main:app --reload --port $PORT --host $HOST




