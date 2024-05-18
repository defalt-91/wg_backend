import re
import uuid
from io import StringIO

from fastapi import APIRouter
from fastapi import (
    Depends
)
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_superuser
from app.crud.crud_peer import crud_peer
from app.crud.crud_wgserver import crud_wg_interface
from app.db.session import get_session
from app.models.peer import Peer
from app.schemas.Peer import PeerOut, PeerUpdate, PeerCreate, PeerRXRT

router = APIRouter()


@router.get(
    "/peers/rxtx",
    response_model=list[PeerRXRT],
    response_model_exclude={"preshared_key"},
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    dependencies=[Depends(get_current_active_superuser)]
)
async def get_peers_rxtx() -> list[PeerRXRT]:
    return crud_wg_interface.get_only_peers()


@router.get(
    "/peers",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[PeerOut],
    response_model_exclude={"public_key"},
)
async def peer_list(db: Session = Depends(get_session)):
    peers, if_config = crud_wg_interface.get_config(db)
    return peers


@router.post(
    "/peer/",
    response_model=PeerOut,
    dependencies=[Depends(get_current_active_superuser)],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    response_model_exclude={
        "public_key",
        "transfer_rx",
        "transfer_tx",
        "last_handshake_at"
    }
)
async def create_peer(
        peer_in: PeerCreate,
        db: Session = Depends(get_session),
):
    server = crud_wg_interface.get_server_config(db)
    peer_in.interface_id = server.id
    new_db_peer = crud_peer.create(db, obj_in=peer_in)
    crud_wg_interface.add_peer(peer=new_db_peer)
    return new_db_peer


@router.put(
    "/peer/{peer_id}",
    response_model=PeerOut,
    dependencies=[Depends(get_current_active_superuser)],
)
async def update_peer(
        peer_id: uuid.UUID,
        peer: PeerUpdate,
        db: Session = Depends(get_session),
):
    db_peer = db.get(Peer, peer_id)
    updated_peer_dict = peer.model_dump(exclude_none=True, exclude_unset=True)
    # updated_peer_dict['allowedIPs'] = ",".join(peer.allowedIPs)
    updated_peer = crud_peer.update(db, db_obj=db_peer, obj_in=updated_peer_dict)
    if not peer.enabled:
        crud_wg_interface.remove_peer(db_peer.public_key)
    else:
        crud_wg_interface.update_peer(updated_peer)
    return updated_peer


@router.delete(
    "/peer/{peer_id}",
    response_model=PeerOut,
    dependencies=[Depends(get_current_active_superuser)],
)
async def delete_peer(peer_id: uuid.UUID, db: Session = Depends(get_session)):
    deleted_peer = crud_peer.remove(db=db, item_id=peer_id)
    crud_wg_interface.remove_peer(deleted_peer.public_key)
    return deleted_peer


@router.get(
    "/peer/{peer_id}/svgqrcode",
    dependencies=[Depends(get_current_active_superuser)],
)
async def create_svg_from_config(
        peer_id: uuid.UUID, db: Session = Depends(get_session)
):
    svg = crud_peer.peer_qrcode_svg(db=db, peer_id=peer_id)
    return Response(
        svg.to_string(), headers={"Content-Type": "image/svg+xml; charset=utf-8"}
    )


@router.get(
    "/peer/{peer_id}/configuration",
    dependencies=[Depends(get_current_active_superuser)],
)
async def peer_configuration(
        peer_id: uuid.UUID, db: Session = Depends(get_session)
):
    peer_config = crud_peer.get_peer_config(db, peer_id)
    peer = crud_peer.get(db, peer_id)
    peer_name = str(peer.name)
    file_name = re.sub("[^a-zA-Z0-9_=+.-]", "-", peer_name)
    file_name = re.sub("(-{2,}|-)", "-", file_name)
    file_name = re.sub("(-)", "", file_name)[:32]
    f = StringIO(peer_config)
    headers = {
        "Content-Disposition": f"attachment; filename={file_name}.conf",
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Length": str(len(f.getvalue())),
    }
    return StreamingResponse(f, headers=headers)
