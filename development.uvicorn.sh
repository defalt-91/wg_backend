
PYTHONBUFFERED=1
PYTHONWRITEBYTECODE=1
PORT=8000
HOST=0.0.0.0
#alembic upgrade head
python backend_pre_start.py
python initial_data.py
# python pre_start.py
.venv/bin/uvicorn app.main:app --reload --port $PORT --host $HOST