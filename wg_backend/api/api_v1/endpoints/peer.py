import re
import uuid
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse

from wg_backend.api import TimedRoute, get_current_active_superuser
from wg_backend.crud.crud_peer import crud_peer
from wg_backend.crud.crud_wgserver import crud_wg_interface
# from wg_backend.crud import crud_peer, crud_wg_interface
from wg_backend.db import SessionDep
from wg_backend.models import Peer, WGInterface
from wg_backend.schemas import (
    DBPlusStdoutPeer, DbDataPeer, PeerCreate, PeerCreateForInterface, PeerUpdate,
    StdoutRxTxPlusLhaPeer
)


peer_router = APIRouter(route_class = TimedRoute)


@peer_router.get(
    "/peers/rxtx",
    response_model = list[StdoutRxTxPlusLhaPeer],
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    dependencies = [Depends(get_current_active_superuser)]
)
async def get_peers_rxtx() -> list[StdoutRxTxPlusLhaPeer]:
    return crud_wg_interface.get_rxtx_lha_config()


@peer_router.get(
    "/peers",
    dependencies = [Depends(get_current_active_superuser)],
    response_model = list[DBPlusStdoutPeer],
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    response_model_exclude = {},
)
async def peer_list(session: SessionDep):
    """
    Peers list
    """
    data = crud_wg_interface.get_full_config(session)
    return list(data.values())


@peer_router.post(
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
        session: SessionDep,
        presharedKey: bool = True,
        interface_id: int | None = 1
):
    """ Create Wireguard interface peer """
    interface = crud_wg_interface.get_if_db(session, interface_id = interface_id)
    new_schema_peer: PeerCreate = PeerCreateForInterface.create_from_if(
        db_if = interface,
        peer_in = peer_in,
    )
    create_dict = new_schema_peer.model_dump()
    if not presharedKey:
        del create_dict['preshared_key']
    new_db_peer = crud_peer.create(session, obj_in = create_dict)
    peers = interface.peers
    crud_wg_interface.sync_peers_config_file_to_interface(peers = peers)
    return new_db_peer


@peer_router.put(
    "/peer/{peer_id}",
    response_model = DBPlusStdoutPeer,
    dependencies = [Depends(get_current_active_superuser)],
)
async def update_peer(
        peer_id: uuid.UUID,
        peer: PeerUpdate,
        session: SessionDep,
):
    db_peer = session.get(Peer, peer_id)
    updated_peer_dict = peer.model_dump(exclude_none = True, exclude_unset = True)
    # updated_peer_dict['allowedIPs'] = ",".join(peer.allowedIPs)
    updated_peer = crud_peer.update(session, db_obj = db_peer, obj_in = updated_peer_dict)
    if not updated_peer.enabled:
        crud_wg_interface.remove_peer_from_if(updated_peer)
    else:
        crud_wg_interface.sync_peers_config_file_to_interface(peers = session.query(WGInterface).one().peers)
    return updated_peer


@peer_router.delete(
    "/peer/{peer_id}",
    response_model = DbDataPeer,
    dependencies = [Depends(get_current_active_superuser)],
)
async def delete_peer(peer_id: uuid.UUID, session: SessionDep):
    deleted_peer = crud_peer.remove(session = session, item_id = peer_id)
    crud_wg_interface.remove_peer_from_if(deleted_peer)
    return deleted_peer


@peer_router.get(
    "/peer/{peer_id}/svgqrcode",
    dependencies = [Depends(get_current_active_superuser)],
)
async def create_svg_from_config(
        peer_id: uuid.UUID, session: SessionDep
):
    svg = crud_peer.peer_qrcode_svg(session = session, peer_id = peer_id)
    return Response(
        svg.to_string(), headers = {"Content-Type": "image/svg+xml; charset=utf-8"}
    )


@peer_router.get(
    "/peer/{peer_id}/configuration",
    dependencies = [Depends(get_current_active_superuser)],
)
async def peer_configuration(
        peer_id: uuid.UUID, session: SessionDep
):
    peer_config = crud_peer.get_peer_config(session, peer_id)
    peer = crud_peer.get(session, peer_id)
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
