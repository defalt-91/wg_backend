from fastapi import APIRouter, Depends, Body

from wg_backend.db.session import get_session
from wg_backend.crud.crud_wgserver import crud_wg_interface
from wg_backend.schemas.wg_interface import WGInterfaceCreate
from sqlalchemy.orm import Session
from wg_backend.api.deps import get_current_active_superuser

router = APIRouter()

"""     for future development      """
@router.post(
    '/create',
    dependencies=[Depends(get_current_active_superuser)],
    response_model=WGInterfaceCreate,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    response_model_exclude={"public_key", "private_key"},
)
async def wireguard_net_interface(
        obj_in: WGInterfaceCreate,
        db: Session = Depends(get_session),
):
    return crud_wg_interface.create(obj_in=obj_in.model_dump(), db=db)


@router.get(
    '/',
    dependencies=[Depends(get_current_active_superuser)],
    response_model=WGInterfaceCreate,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    response_model_exclude={"public_key", "private_key"},
)
async def get_wireguard_net_interface(
        wireguard_network_interface_id: int,
        db: Session = Depends(get_session),
):
    return crud_wg_interface.get_object_or_404(db, wireguard_network_interface_id)
