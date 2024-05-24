import contextlib
import logging
from typing import AsyncIterator

from wg_backend.core.configs.Settings import execute, get_settings
from wg_backend.crud.crud_wgserver import crud_wg_interface
from wg_backend.db.session import SessionFactory
from fastapi import FastAPI
from fastapi.datastructures import State

settings = get_settings()

logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def wg_quick_lifespan(application: FastAPI) -> AsyncIterator[State]:
    logger.debug("creating wireguard interface with loaded config from db ...")
    with SessionFactory() as db:
        cmd = ["sudo", "wg", "show", settings.WG_INTERFACE_NAME]
        proc = execute(cmd)
        stderr = proc.stderr
        return_code = proc.returncode
        if not return_code:
            logger.warning(f"there is a wireguard interface up with name of {settings.WG_INTERFACE_NAME}, trying to down it ...")
            execute(["sudo", "wg-quick", "down", settings.wg_if_config_file_path])
            logger.warning("downed it with return code of:", )
        if return_code and 'Operation not permitted' in stderr:
            raise PermissionError('You should run this wg_backend with root privileges')
        elif return_code and 'No such device' not in stderr:
            raise Exception(
                f"WireGuard exited with the error: Cannot find device {settings.WG_INTERFACE_NAME}This usually means that "
                f"your host's kernel does not support WireGuard!", stderr
            )
        crud_wg_interface.create_wg_quick_config_file(session = db, interface_id = 1)
        up_proc = execute(["sudo", "wg-quick", "up", settings.wg_if_config_file_path])
        if up_proc.returncode != 0:
            logger.critical(f"Loading peers file config to wg interface failed. error: {up_proc.stderr}")
        else:
            logger.debug(f"Loading peers file config to wg interface succeed.")
    yield
    execute(["sudo", "wg-quick", "down", settings.wg_if_config_file_path])
