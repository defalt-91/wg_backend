# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.registry import Base  # noqa
from app.models.client import Client  # noqa
from app.models.user import User  # noqa
from app.models.wgserver import WGServer  # noqa
