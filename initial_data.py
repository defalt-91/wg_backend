import logging

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from app.core.Settings import get_settings
from app.crud.crud_user_fn import authenticate, create_user
from app.crud.crud_wgserver import crud_wg_interface
from app.db.session import SessionFactory
from app.schemas import UserCreate
from app.schemas.wg_interface import WGInterfaceCreate

settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """creating superuser if there is not one"""
    user = authenticate(
        session=db,
        username=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PASSWORD,
    )
    if not user:
        logger.debug("No superuser,creating one from provided environments ...")
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        super_user = create_user(session=db, user_create=user_in)
        logger.debug(f"newly created superuser is: {super_user.username}")
        logger.debug("Superuser created")
    else:
        logger.debug("superuser already exists.")
    """ load peer config from db or create one"""
    orm_wg_server = None
    try:
        orm_wg_server = crud_wg_interface.get_one(session=db)
        logger.debug("loading existing interface from database.")
    except NoResultFound:
        logger.debug("No interface configuration found in database, creating one ...")
        obj_in = WGInterfaceCreate(interface=settings.WG_INTERFACE).model_dump()
        orm_wg_server = crud_wg_interface.create(db, obj_in=obj_in)
        db.add(orm_wg_server)
        # db.flush()
        db.commit()
        logger.debug("Wireguard db interface created.")
    except MultipleResultsFound:
        logger.debug("there are multiple interfaces in database, loading last one ...")
        orm_wg_server = crud_wg_interface.get_multi(db=db).pop()
    except Exception as e:
        logger.critical('there is a problem loading interface configs from db', e)
    finally:
        logger.debug(f"writing interface config to {settings.wg_if_file_path}")
        crud_wg_interface.create_wg_quick_config_file(orm_server=orm_wg_server)
        logger.debug(f"writing down wireguard db interface with id={orm_wg_server.id} completed.")


if __name__=="__main__":
    logger.info("Creating initial data")
    with SessionFactory() as session:
        init_db(session)
    logger.info("Initial data created")
