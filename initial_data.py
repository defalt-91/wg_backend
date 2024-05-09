import logging
from app.core.Settings import get_settings
from app.crud.crud_wgserver import crud_wgserver
from app.db.session import SessionFactory
from sqlalchemy.orm import Session
from app.crud import user as user_dal
from app.core.Settings import get_settings
from app.models.wgserver import WGServer
from app.schemas import UserCreate
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound

from app.schemas.wgserver import WGServerCreate
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
settings=get_settings()


def init_db(db: Session) -> None:
    """ creating superuser if there is not one  """
    user = user_dal.authenticate(db, username=settings.FIRST_SUPERUSER,password=settings.FIRST_SUPERUSER_PASSWORD)
    if not user:
        logger.info("No superuser,creating one from provided environments ...")
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        super_user = user_dal.create(db, obj_in=user_in)
        logger.info(f"newly created superuser is: {super_user.username}")
    
    """ load client config from db or create one"""
    try:
        orm_wg_server=db.query(WGServer).one()
        logger.info("loading existing server from database")
    except NoResultFound:
        logger.info("No server configuration in database, creating one ...")
        orm_wg_server = WGServer(**WGServerCreate().model_dump())
        db.add(orm_wg_server)    
        db.commit()
        
    except MultipleResultsFound:
        logger.info("there are multiple servers in database, loading last one ...")
        orm_wg_server=db.query(WGServer).all().pop()
    finally:
        crud_wgserver.create_write_wgserver_conf_from_orm(orm_server=orm_wg_server)
        crud_wgserver.create_peers_str(orm_wg_server.clients)        
        crud_wgserver.sync_wg_quicks_strip()
    
    
if __name__ == "__main__":
    logger.info("Creating initial data")
    with SessionFactory() as session:
        init_db(session)
    logger.info("Initial data created")