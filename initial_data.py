import logging

from sqlalchemy.orm import Session
from sqlalchemy.orm import exc as sqlalchemy_exceptions

from wg_backend.core.settings import get_settings
from wg_backend.crud.crud_user_fn import authenticate, create_user
from wg_backend.crud.crud_wgserver import crud_wg_interface
from wg_backend.db.session import SessionFactory
from wg_backend.models.wg_interface import WGInterface
from wg_backend.schemas.user import UserCreate
from wg_backend.schemas.wg_interface import WGInterfaceCreate

settings = get_settings()
logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """creating superuser if there is not one"""
    user = authenticate(
        session = db,
        username = settings.FIRST_SUPERUSER,
        password = settings.FIRST_SUPERUSER_PASSWORD,
    )
    if not user:
        logger.debug("No superuser,creating one from provided environments ...")
        user_in = UserCreate(
            username = settings.FIRST_SUPERUSER,
            password = settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser = True,
        )
        super_user = create_user(session = db, user_create = user_in)
        logger.debug(f"newly created superuser is: {super_user.username}")
        logger.debug("Superuser created.")
    else:
        logger.debug("superuser already exists.")
    """ load peer config from db or create one"""
    try:
        interface = session.query(WGInterface).one()
        logger.debug(f"loading existing {interface.interface} config from database.")
    except sqlalchemy_exceptions.NoResultFound:
        logger.debug("No interface configuration found in database, creating one ...")
        obj_in = WGInterfaceCreate(interface = settings.WG_INTERFACE_NAME).model_dump()
        created_orm_wg_if = crud_wg_interface.create(db, obj_in = obj_in)
        logger.info("Wireguard db interface created.")
        logger.info(f"newly created interface in db is => {created_orm_wg_if.interface}.")
    except sqlalchemy_exceptions.MultipleResultsFound:
        logger.debug("there are multiple interfaces in database.")
    finally:
        logger.debug("everything is ready for wg_backend to start.")


if __name__ == "__main__":
    logger.info("Creating initial data")
    with SessionFactory() as session:
        init_db(session)
    logger.info("Initial data created")
