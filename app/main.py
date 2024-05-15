import contextlib, subprocess, logging,pyroute2
from typing import AsyncIterator
from fastapi import FastAPI
from fastapi.datastructures import State
from starlette.middleware.cors import CORSMiddleware
from app.api.api_v1.api import api_router
from app.crud.crud_wgserver import crud_wgserver
from app.models.client import Client
from .db.session import SessionFactory, engine
from app.db.registry import mapper_registry
from app.core.Settings import get_settings

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
settings = get_settings()


@contextlib.asynccontextmanager
async def wg_quick_lifespan(app: FastAPI) -> AsyncIterator[State]:
    logger.info("creating wireguard interface with loaded config from db ...")
    db = SessionFactory()
    try:
        if not subprocess.run(
            ["wg", "show", settings.WG_INTERFACE], capture_output=True, text=True
        ).stderr:
            logger.warning(
                f"==> there is a wireguard interface with name off {settings.WG_INTERFACE}, trying to down it ... "
            )
            subprocess.run(["wg-quick", "down", settings.WG_INTERFACE])
        subprocess.run(["wg-quick", "up", settings.wgserver_file_path])
        # logger.info("loading peers file config (wg addconf) to wg service ...")
        crud_wgserver.sync_db_peers_to_wg(db)

    except pyroute2.NetlinkError as err:
        # if (
        #     err
        #     and err.message
        #     and err.message.includes(f'Cannot find device "{settings.WG_INTERFACE}"')
        # ):
        raise Exception(
                f"WireGuard exited with the error: Cannot find device {settings.WG_INTERFACE}This usually means that your host's kernel does not support WireGuard!",err
            )
    finally:
        db.close()
    yield
    subprocess.run(["wg-quick", "down", settings.WG_INTERFACE])


mapper_registry.metadata.create_all(bind=engine)
app = FastAPI(
    debug=settings.DEBUG,
    title=settings.PROJECT_NAME,
    version="1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{'/api/v1'}/openapi.json",
    root_path="/api",
    lifespan=wg_quick_lifespan,
    # root_path="/api/v1"  # for behind proxy
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)

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
