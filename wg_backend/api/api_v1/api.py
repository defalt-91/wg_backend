from fastapi import APIRouter

from wg_backend.api.api_v1.endpoints import login
from wg_backend.api.api_v1.endpoints import peer
from wg_backend.api.api_v1.endpoints import users
from wg_backend.api.api_v1.endpoints import wg_interface

v1_api_router = APIRouter(redirect_slashes = False, prefix = "")

v1_api_router.include_router(
    router = login.router,
    tags = ["login"],
    prefix = "",
    include_in_schema = True,
    deprecated = False,
)
v1_api_router.include_router(
    router = users.router,
    prefix = "/users",
    tags = ["users"],
    include_in_schema = True,
    deprecated = False,
)
v1_api_router.include_router(
    peer.router,
    prefix = "",
    tags = ["Peers"],
    include_in_schema = True,
    deprecated = False,
)
v1_api_router.include_router(
    wg_interface.router,
    prefix = "/wgif",
    tags = ["WG_Interface", "in development"],
    include_in_schema = True,
    deprecated = False,
)
