# Import all the models, so that Base has them before being
# imported by Alembic
from app.models.peer import Peer  # noqa
from app.models.user import User  # noqa
from app.models.wg_interface import WGInterface  # noqa
