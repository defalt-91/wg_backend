import contextlib
import logging
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.datastructures import State

from wg_backend.core.settings import execute, get_settings
from wg_backend.crud.crud_wgserver import crud_wg_interface
from wg_backend.db.session import SessionFactory

settings = get_settings()

logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def wg_quick_lifespan(application: FastAPI) -> AsyncIterator[State]:
    logger.debug("creating wireguard interface with loaded config from db ...")
    with SessionFactory() as session:
        cmd = ["sudo", "wg", "show", settings.WG_INTERFACE_NAME]
        proc = execute(cmd)
        stderr = proc.stderr
        return_code = proc.returncode
        if not return_code:
            logger.warning(
                f"there is a wireguard interface up "
                f"with name of {settings.WG_INTERFACE_NAME}, trying to down it ..."
            )
            rc = execute(["sudo", "wg-quick", "down", settings.wg_if_config_file_path])
            logger.warning(f"downed it with return code = {rc.returncode}")
        if return_code and 'Operation not permitted' in stderr:
            raise PermissionError('You should run this wg_backend with root privileges')
        elif return_code and 'No such device' not in stderr:
            raise Exception(
                f"WireGuard exited with the error: Cannot find "
                f"device {settings.WG_INTERFACE_NAME}This usually means that "
                f"your host's kernel does not support WireGuard!", stderr
            )
        db_wg_if = crud_wg_interface.get(session = session, item_id=1)
        crud_wg_interface.create_write_wg_quick_config_file(db_wg_if=db_wg_if)
        if db_wg_if.peers:
            crud_wg_interface.create_write_peers_config_file(peers=db_wg_if.peers)
        up_proc = execute(["sudo", "wg-quick", "up", settings.wg_if_config_file_path])
        if up_proc.returncode:
            logger.critical(f"Loading peers file config to wg interface failed. error: \n\t {up_proc.stderr}")
        else:
            logger.debug(f"Syncing wg interface with database interface and peers completed.")
        session.close_all()
    yield
    execute(["sudo", "wg-quick", "down", settings.wg_if_config_file_path])
