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

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
settings = get_settings()


@contextlib.asynccontextmanager
async def wg_quick_lifespan(application: FastAPI) -> AsyncIterator[State]:
    logger.info("creating wireguard interface with loaded config from db ...")
    db = SessionFactory()
    try:
        std_return_code = subprocess.run(["wg", "show", settings.WG_INTERFACE],capture_output=False, stdout=subprocess.PIPE).returncode
        if std_return_code != 0:
            logger.debug(f"there is a wireguard interface with name of {settings.WG_INTERFACE}, trying to down it ... ")
            subprocess.run(["wg-quick", "down", settings.WG_INTERFACE])
            logger.warning("downed it")
        subprocess.run(["wg-quick", "up", settings.wgserver_file_path])
        # logger.info("loading peers file config (wg addconf) to wg service ...")
        crud_wg_interface.sync_db_peers_to_wg(db)
    except pyroute2.NetlinkError as err:
        raise Exception(
            f"WireGuard exited with the error: Cannot find device {settings.WG_INTERFACE}This usually means that "
            f"your host's kernel does not support WireGuard!", err
        )
    finally:
        db.close()
    yield
    # subprocess.run(["wg-quick", "save", settings.WG_INTERFACE])
    subprocess.run(["wg-quick", "down", settings.WG_INTERFACE])


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
