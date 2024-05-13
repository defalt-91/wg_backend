import contextlib,subprocess,logging
from typing import AsyncIterator
from fastapi import FastAPI,staticfiles,utils
from fastapi.datastructures import State
from starlette.middleware.cors import CORSMiddleware
from app.api.api_v1.api import api_router
from .db.session import engine
from app.db.registry import mapper_registry
from app.core.Settings import get_settings

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
settings=get_settings()

@contextlib.asynccontextmanager
async def wg_quick_lifespan(app: FastAPI) -> AsyncIterator[State]:
    logger.info("starting wireguard interface with newly writed config ...")
    try:
        subprocess.run(['wg-quick', 'up' ,'wg0']).stdout
    except Exception as err:
        if err and err.message and err.message.includes('Cannot find device "wg0"'):
            raise Exception('WireGuard exited with the error: Cannot find device "wg0"\nThis usually means that your host\'s kernel does not support WireGuard!',)
    # server = WireguardNetlinkDevice(settings.WG_INTERFACE)
    # with SessionContextManager() as db:
    yield {}

    # peer_file_data = []
    # db:Session = get_session()
    # db_clients = db.get(wgserver,id=1).clients
    # for peer in server.get_config().peers:
    #     print(peer)
    #     peer_file_data.extend(server.get_config().peers[peer].as_wgconfig_snippet())
    # with open(f"{settings.WG_CONFIGPATH}{settings.WG_INTERFACE}-peers.conf", mode='w', encoding='utf-8') as peers_fh:
    #     peers_fh.write(os.linesep.join(peer_file_data))
    subprocess.run(['wg-quick', 'down',settings.WG_INTERFACE])

mapper_registry.metadata.create_all(bind=engine)
app = FastAPI(
	debug=settings.DEBUG,
	title=settings.PROJECT_NAME,
	version="1",
	docs_url="/docs",
	redoc_url="/redoc",
	openapi_url=f"{'/api/v1'}/openapi.json",
	root_path='/api',
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
#         request.state.db.commit()
#     finally:
#         request.state.db.close()
#     return response
