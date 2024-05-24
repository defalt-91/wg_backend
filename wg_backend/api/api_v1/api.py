from fastapi import APIRouter

from . import login_router, peer_router, user_router, wg_if_router

v1_api_router = APIRouter(redirect_slashes = False, prefix = "")

v1_api_router.include_router(
    router = login_router,
    tags = ["login"],
    prefix = "",
    include_in_schema = True,
    deprecated = False,
)
v1_api_router.include_router(
    router = user_router,
    prefix = "/users",
    tags = ["users"],
    include_in_schema = True,
    deprecated = False,
)
v1_api_router.include_router(
    peer_router,
    prefix = "",
    tags = ["Peers"],
    include_in_schema = True,
    deprecated = False,
)
v1_api_router.include_router(
    wg_if_router,
    prefix = "/wgif",
    tags = ["WG_Interface", "in development"],
    include_in_schema = True,
    deprecated = False,
)
