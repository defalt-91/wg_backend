from fastapi.routing import APIRoute
from typing import Callable
from fastapi import Request, Response, APIRouter
from app.api.api_v1.endpoints import login, users, peer, wg_interface
import time


class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = time.time() - before
            response.headers["X-Response-Time"] = str(duration)
            return response

        return custom_route_handler


api_router = APIRouter(redirect_slashes=False, route_class=TimedRoute, prefix="/v1")


api_router.include_router(
    router=login.router,
    tags=["login"],
    prefix="",
    include_in_schema=True,
    deprecated=False,
)
api_router.include_router(
    router=users.router,
    prefix="/users",
    tags=["users"],
    include_in_schema=True,
    deprecated=False,
)
api_router.include_router(
    peer.router,
    prefix="",
    tags=["Peers"],
    include_in_schema=True,
    deprecated=False,
)
api_router.include_router(
    wg_interface.router,
    prefix="/wgif",
    tags=["WG_Interface", "in development"],
    include_in_schema=True,
    deprecated=False,
)
