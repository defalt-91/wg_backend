import logging
from typing import Type

from sqlalchemy.orm import Session
from wg_backend.core.settings import get_settings
from wg_backend.crud.base import CRUDBase
from wg_backend.models.wg_interface import WGInterface
from wg_backend.schemas.wg_interface import WGInterfaceCreate, WGInterfaceUpdate


settings = get_settings()
logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class CRUDWGInterface(CRUDBase[WGInterface, WGInterfaceCreate, WGInterfaceUpdate]):
    def get_db_if(self, session: Session, interface_id: int) -> Type[WGInterface] | None:
        return session.query(self.model).get(ident = interface_id)

    def get_if_private_key(self, session: Session, interface_id: int) -> Type[WGInterface] | None:
        return session.query(self.model).get(ident = interface_id)


crud_wg_interface = CRUDWGInterface(WGInterface)
