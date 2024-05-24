import logging

from fastapi import FastAPI
from starlette.middleware import cors, trustedhost  # gzip,; sessions,; authentication

from wg_backend.api.api_v1.api import v1_api_router
from wg_backend.core.settings import get_settings
from wg_backend.middlewares import wg_quick_lifespan


settings = get_settings()

logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    debug = settings.DEBUG,
    title = settings.PROJECT_NAME,
    version = "1",
    docs_url = "/docs",
    redoc_url = "/redoc",
    openapi_url = "/openapi.json",
    root_path = settings.API_ADDRESS,
    lifespan = wg_quick_lifespan,
    # root_path="/api/v1"  # for behind proxy
)

# wg_backend.add_middleware(
#     ExtraResponseHeadersMiddleware,
#     headers = MutableHeaders()
# )


# Set all CORS enabled origins
app.add_middleware(
    cors.CORSMiddleware,
    allow_origins = settings.BACKEND_CORS_ORIGINS,
    allow_credentials = True,
    # allow_origin_regex = ,
    # expose_headers=(,),
    allow_methods = ["*"],
    allow_headers = ["X-Response-Time", "*"],
)

app.add_middleware(
    trustedhost.TrustedHostMiddleware,
    allowed_hosts = settings.BACKEND_ALLOWED_HOSTS
)

app.include_router(v1_api_router)

# wg_backend.route()
# @wg_backend.middleware("http")
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
