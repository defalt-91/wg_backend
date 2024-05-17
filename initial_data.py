from app.crud.crud_wgserver import crud_wg_interface
from app.db.session import SessionFactory
from sqlalchemy.orm import Session
from app.crud import user as user_dal
from app.core.Settings import get_settings
from app.models.wg_interface import WGInterface
from app.schemas import UserCreate
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from app.schemas.wg_interface import WGInterfaceCreate
import logging

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
settings = get_settings()


def init_db(db: Session) -> None:
    """creating superuser if there is not one"""
    user = user_dal.authenticate(
        db,
        username=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PASSWORD,
    )
    if not user:
        logger.info("No superuser,creating one from provided environments ...")
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        super_user = user_dal.create(db, obj_in=user_in)
        logger.debug(f"newly created superuser is: {super_user.username}")
        logger.info("Superuser created")
    else:
        logger.debug("superuser already exists.")
    """ load peer config from db or create one"""
    orm_wg_server = None
    try:
        orm_wg_server = crud_wg_interface.get_one(session=db)
        logger.debug("loading existing interface from database.")
    except NoResultFound:
        logger.info("No interface configuration found in database, creating one ...")
        obj_in = WGInterfaceCreate(interface=settings.WG_INTERFACE).model_dump()
        orm_wg_server = crud_wg_interface.create(db, obj_in=obj_in)
        db.add(orm_wg_server)
        # db.flush()
        db.commit()
        logger.info("Wireguard db interface created.")
    except MultipleResultsFound:
        logger.debug("there are multiple interfaces in database, loading last one ...")
        orm_wg_server = crud_wg_interface.get_multi(db=db).pop()
    finally:
        logger.debug(f"writing interface config to {settings.wgserver_file_path}")
        result = crud_wg_interface.create_write_wgserver_file(orm_server=orm_wg_server)
        logger.debug(f"writing down wireguard db interface with id={orm_wg_server.id} completed.")


if __name__ == "__main__":
    logger.info("Creating or loading initial superuser and interface from environments")
    with SessionFactory() as session:
        init_db(session)
    logger.info("Initial superuser and wireguard interface config are present in db.")
