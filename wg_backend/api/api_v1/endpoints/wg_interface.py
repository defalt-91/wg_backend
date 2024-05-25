from fastapi import APIRouter, Depends

from wg_backend.api.deps import get_current_active_superuser
from wg_backend.crud.crud_wgserver import crud_wg_interface
from wg_backend.db.session import SessionDep
from wg_backend.schemas.wg_interface import WGInterfaceCreate

wg_if_router = APIRouter()


# for future development


@wg_if_router.post(
    '/create',
    dependencies = [Depends(get_current_active_superuser)],
    response_model = WGInterfaceCreate,
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    response_model_exclude = {"public_key", "private_key"},
)
async def wireguard_net_interface(
        obj_in: WGInterfaceCreate,
        session: SessionDep,
):
    return crud_wg_interface.create(obj_in = obj_in.model_dump(), session = session)


@wg_if_router.get(
    '/',
    dependencies = [Depends(get_current_active_superuser)],
    response_model = WGInterfaceCreate,
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    response_model_exclude = {"public_key", "private_key"},
)
async def get_wireguard_net_interface(
        wireguard_network_interface_id: int,
        session: SessionDep,
):
    return crud_wg_interface.get_object_or_404(session, wireguard_network_interface_id)
