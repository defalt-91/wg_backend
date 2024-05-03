from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.api_v1.api import api_router
from .db.session import engine
from fastapi import FastAPI
from .db.session import engine
from app.db.registry import mapper_registry
from app.core.Settings import get_settings
import subprocess

settings=get_settings()

    
mapper_registry.metadata.create_all(bind=engine)
app = FastAPI(
	debug=settings.DEBUG,
	title=settings.PROJECT_NAME,
	version="1",
	docs_url="/docs",
	redoc_url="/redoc",
	openapi_url=f"{'/api/v1'}/openapi.json",
	root_path='/api',
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
app.add_event_handler("shutdown",lambda:subprocess.run(['wg-quick', 'down', 'wg0']))
# @app.middleware("http")
# async def db_session_middleware(request: Request, call_next):
#     response = Response("Internal server error", status_code=500)
#     try:
#         request.state.db = SessionFactory()
#         response = await call_next(request)
#     except:
#         request.state.db.rollback()
#         raise
#     else:
#         request.state.db.commit()
#     finally:
#         request.state.db.close()
#     return response
