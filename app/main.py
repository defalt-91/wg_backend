import contextlib
import logging
import subprocess
from typing import AsyncIterator

import pyroute2
from fastapi import FastAPI
from fastapi.datastructures import State
from starlette.middleware import (
    cors,
    trustedhost,
    # gzip,
    # sessions,
    # authentication
)

from app.api.api_v1.api import v1_api_router
from app.core.Settings import get_settings
from app.crud.crud_wgserver import crud_wg_interface
from app.db.session import SessionFactory

settings = get_settings()

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def wg_quick_lifespan(application: FastAPI) -> AsyncIterator[State]:
    logger.info("creating wireguard interface with loaded config from db ...")
    db = SessionFactory()
    try:
        # std = subprocess.run(["wg", "show", settings.WG_INTERFACE], capture_output=True)
        # if std.stderr and 'Operation not permittesd' in std.stderr.decode().strip():
        #     raise PermissionError('You should run this app with root privileges')
        # elif std.stderr and 'interface:' in std.stdout.decode().strip():
        #     logger.warning(f"there is a wireguard interface with name of {settings.WG_INTERFACE}, trying to down it ...")
        #     subprocess.run(["wg-quick", "down", settings.wg_if_file_path])
        #     logger.warning("downed it")
        # elif std.stderr and 'No such device' not in std.stderr.decode().strip():
        #     raise RuntimeError(std.stderr.decode().strip())
        subprocess.run(["wg-quick", "up", settings.wg_if_file_path])
        logger.debug("loading peers file config (wg addconf) to wg service ...")
        crud_wg_interface.sync_db_peers_to_wg(db)
    except pyroute2.NetlinkError as err:
        raise Exception(
            f"WireGuard exited with the error: Cannot find device {settings.WG_INTERFACE}This usually means that "
            f"your host's kernel does not support WireGuard!", err
        )
    finally:
        db.close()
    yield
    subprocess.run(["wg-quick", "save", settings.wg_if_file_path])
    subprocess.run(["wg-quick", "down", settings.wg_if_file_path])


app = FastAPI(
    debug=settings.DEBUG,
    title=settings.PROJECT_NAME,
    version="1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path=settings.API_ADDRESS,
    lifespan=wg_quick_lifespan,
    # root_path="/api/v1"  # for behind proxy
)

# Set all CORS enabled origins
app.add_middleware(
    cors.CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["X-Response-Time", "*"],
)
app.add_middleware(
    trustedhost.TrustedHostMiddleware,
    allowed_hosts=settings.BACKEND_ALLOWED_HOSTS
)

app.include_router(v1_api_router)

# app.route()
# @app.middleware("http")
# async def db_session_middleware(request: Request, call_next):
#     response = Response("Internal server error", status_code=500)
#     try:
#         request.state.db = get_session()
#         response = await call_next(request)
#     except:
#         request.state.db.rollback()
#         raise
#     else:
#         request.state.db.flush()
#     finally:
#         request.state.db.close()
#     return response
