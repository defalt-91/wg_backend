import re
import uuid
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse

from wg_backend.api.deps import get_current_active_superuser
from wg_backend.api.utils import TimedRoute
from wg_backend.crud.crud_peer import crud_peer
from wg_backend.crud.crud_wgserver import crud_wg_interface
from wg_backend.db.session import SessionDep
from wg_backend.models.peer import Peer
from wg_backend.models.wg_interface import WGInterface
from wg_backend.schemas.Peer import DBPlusStdoutPeer, DbDataPeer, PeerCreate, PeerCreateForInterface, PeerUpdate, \
    StdoutRxTxPlusLhaPeer


router = APIRouter(route_class = TimedRoute)


@router.get(
    "/peers/rxtx",
    response_model = list[StdoutRxTxPlusLhaPeer],
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    dependencies = [Depends(get_current_active_superuser)]
)
async def get_peers_rxtx() -> list[StdoutRxTxPlusLhaPeer]:
    return crud_wg_interface.get_rxtx_lha_config()


@router.get(
    "/peers",
    dependencies = [Depends(get_current_active_superuser)],
    response_model = list[DBPlusStdoutPeer],
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    response_model_exclude = { },
)
async def peer_list(session: SessionDep):
    """
    Peers list
    """
    data = crud_wg_interface.get_full_config(session)
    return list(data.values())


@router.post(
    "/peer/",
    response_model = DbDataPeer,
    dependencies = [Depends(get_current_active_superuser)],
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    response_model_exclude = {
        # "public_key",
        # "transfer_rx",
        # "transfer_tx",
        # "last_handshake_at"
    },
)
async def create_peer(
        peer_in: PeerCreate,
        db: SessionDep,
        presharedKey: bool = True,
        interface_id: int | None = 1
):
    """ Create Wireguard interface peer """
    interface = crud_wg_interface.get_if_db(db, interface_id = interface_id)
    new_schema_peer: PeerCreate = PeerCreateForInterface.create_from_if(
        db_if = interface,
        peer_in = peer_in,
    )
    create_dict = new_schema_peer.model_dump()
    if not presharedKey:
        del create_dict['preshared_key']
    new_db_peer = crud_peer.create(db, obj_in = create_dict)
    peers = interface.peers
    crud_wg_interface.sync_peers_config_file_to_interface(peers = peers)
    return new_db_peer


@router.put(
    "/peer/{peer_id}",
    response_model = DBPlusStdoutPeer,
    dependencies = [Depends(get_current_active_superuser)],
)
async def update_peer(
        peer_id: uuid.UUID,
        peer: PeerUpdate,
        db: SessionDep,
):
    db_peer = db.get(Peer, peer_id)
    updated_peer_dict = peer.model_dump(exclude_none = True, exclude_unset = True)
    # updated_peer_dict['allowedIPs'] = ",".join(peer.allowedIPs)
    updated_peer = crud_peer.update(db, db_obj = db_peer, obj_in = updated_peer_dict)
    if not updated_peer.enabled:
        crud_wg_interface.remove_peer_from_if(updated_peer)
    else:
        crud_wg_interface.sync_peers_config_file_to_interface(peers = db.query(WGInterface).one().peers)
    return updated_peer


@router.delete(
    "/peer/{peer_id}",
    response_model = DbDataPeer,
    dependencies = [Depends(get_current_active_superuser)],
)
async def delete_peer(peer_id: uuid.UUID, db: SessionDep):
    deleted_peer = crud_peer.remove(db = db, item_id = peer_id)
    crud_wg_interface.remove_peer_from_if(deleted_peer)
    return deleted_peer


@router.get(
    "/peer/{peer_id}/svgqrcode",
    dependencies = [Depends(get_current_active_superuser)],
)
async def create_svg_from_config(
        peer_id: uuid.UUID, db: SessionDep
):
    svg = crud_peer.peer_qrcode_svg(db = db, peer_id = peer_id)
    return Response(
        svg.to_string(), headers = { "Content-Type": "image/svg+xml; charset=utf-8" }
    )


@router.get(
    "/peer/{peer_id}/configuration",
    dependencies = [Depends(get_current_active_superuser)],
)
async def peer_configuration(
        peer_id: uuid.UUID, db: SessionDep
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
    return StreamingResponse(f, headers = headers)
