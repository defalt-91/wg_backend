# Import all the models, so that Base has them before being
# imported by Alembic
from wg_backend.models.peer import Peer  # noqa
from wg_backend.models.user import User  # noqa
from wg_backend.models.wg_interface import WGInterface  # noqa
