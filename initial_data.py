import logging

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from wg_backend.core.configs.Settings import get_settings
from wg_backend.crud.crud_user_fn import authenticate, create_user
from wg_backend.crud.crud_wgserver import crud_wg_interface
from wg_backend.db.session import SessionFactory
from wg_backend.schemas import UserCreate
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
        logger.debug("Superuser created")
    else:
        logger.debug("superuser already exists.")
    """ load peer config from db or create one"""
    try:
        interface = crud_wg_interface.get_one(session = db)
        logger.debug("loading existing interface from database.")
    except NoResultFound:
        logger.debug("No interface configuration found in database, creating one ...")
        obj_in = WGInterfaceCreate(interface = settings.WG_INTERFACE_NAME).model_dump()
        orm_wg_server = crud_wg_interface.create(db, obj_in = obj_in)
        logger.debug("Wireguard db interface created.")
    except MultipleResultsFound:
        logger.debug("there are multiple interfaces in database, loading last one ...")
        # orm_wg_server = crud_wg_interface.get_multi(db=db).pop()
    except Exception as e:
        logger.critical('there is a problem loading interface configs from db', e)
    finally:
        # interface = db.query(interface).one()
        # crud_wg_interface.create_wg_quick_config_file(session = db,interface_id=1)
        logger.debug("everything is ready for wg_backend to start.")


if __name__ == "__main__":
    logger.info("Creating initial data")
    with SessionFactory() as session:
        init_db(session)
    logger.info("Initial data created")
