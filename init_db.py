from sqlalchemy.orm import Session
from app.crud import user as user_dal
from app.crud.crud_wgserver import crud_wgserver
from app.core.Settings import get_settings
from app.models.wgserver import WGServer
from app.schemas.wgserver import WGServerCreate
from app.schemas import UserCreate
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


settings=get_settings()

def init_db(db: Session) -> None:
    """ creating superuser if there is not one  """
    user = user_dal.authenticate(db, username=settings.FIRST_SUPERUSER,password=settings.FIRST_SUPERUSER_PASSWORD)
    if not user:
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user_dal.create(db, obj_in=user_in)

    """ load client config from db or create one"""
    orm_wg_server = crud_wgserver.get_server_config(session=db)
    if not orm_wg_server:
        logger.info('No server configuration in database, creating one ...')
        new_server_conf:WGServerCreate = crud_wgserver.new_server_credentials()
        orm_wg_server = WGServer(**new_server_conf.model_dump())
        db.add(orm_wg_server)
        db.commit()
        # db.refresh
    crud_wgserver.save_wgserver_dot_conf(orm_server=orm_wg_server)
    try:
        subprocess.run(['wg-quick', 'down','wg0']).stdout
        subprocess.run(['wg-quick', 'up' ,'wg0']).stdout
    except Exception as err:
        if err and err.message and err.message.includes('Cannot find device "wg0"'):
            raise Exception('WireGuard exited with the error: Cannot find device "wg0"\nThis usually means that your host\'s kernel does not support WireGuard!',e)
        raise Exception('WireGuard exited with the error: Cannot find device "wg0"\nThis usually means that your host\'s kernel does not support WireGuard!')
    crud_wgserver.sync_wg_quicks_strip()