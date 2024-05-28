import re
import uuid
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from wg_backend.api import exceptions, utils
from wg_backend.api.deps import get_current_active_superuser
from wg_backend.crud.crud_peer import crud_peer
from wg_backend.crud.crud_wgserver import crud_wg_interface
from wg_backend.db.session import SessionDep
from wg_backend.models.peer import Peer
from wg_backend.schemas.Peer import (
    DBPlusStdoutPeer,
    DbDataPeer,
    PeerCreate,
    PeerCreateForInterface,
    PeerUpdate,
    StdoutRxTxPlusLhaPeer
)

peer_router = APIRouter(route_class = utils.TimedRoute)


@peer_router.get(
    "/peers/rxtx",
    response_model = list[StdoutRxTxPlusLhaPeer],
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    dependencies = [Depends(get_current_active_superuser)]
)
async def get_peers_rxtx() -> list[StdoutRxTxPlusLhaPeer]:
    lha_proc = utils.wg_show_lha_cmd()
    transfer_proc = utils.wg_show_transfer_cmd()
    if transfer_proc.stderr or lha_proc.stderr:
        raise exceptions.wg_dump_error(transfer_proc.stderr)
    return utils.get_rxtx_lha_config(transfer_proc.stdout, lha_proc.stdout)


@peer_router.get(
    "/peers",
    dependencies = [Depends(get_current_active_superuser)],
    response_model = list[DBPlusStdoutPeer],
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    # response_model_exclude = {},
)
async def peer_list(session: SessionDep) -> list[DBPlusStdoutPeer]:
    """ Peers list """
    stmt = select(Peer.id, Peer.public_key, Peer.name, Peer.enabled, Peer.created_at, Peer.updated_at)
    peers_db_data = session.execute(stmt).fetchall()
    dump_result = utils.wg_show_dump_cmd()
    data = utils.get_full_config(peers_db_data = peers_db_data, dump_result = dump_result)
    if not data:
        raise exceptions.server_error(f"can't run wg dump data command.")
    return list(data.values())


@peer_router.post(
    "/peer/",
    response_model = DbDataPeer,
    dependencies = [Depends(get_current_active_superuser)],
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    # response_model_exclude = {},
)
async def create_peer(
        peer_in: PeerCreate,
        session: SessionDep,
        preshared_key: bool = True,
        interface_id: int | None = 1
) -> DbDataPeer:
    """ Create Wireguard interface peer """
    interface = crud_wg_interface.get_db_if(session, interface_id = interface_id)
    new_schema_peer: PeerCreateForInterface = PeerCreateForInterface.create_from_if(
        db_if = interface,
        peer_in = peer_in
    )
    create_dict = new_schema_peer.model_dump()
    if not preshared_key:
        del create_dict['preshared_key']
    stmt = select(Peer.address)
    peer_addresses = session.execute(stmt).scalars()
    addresses_set = set(peer_addresses)
    new_ip_address = utils.generate_new_address(addresses_set)
    if not new_ip_address:
        raise exceptions.wg_max_num_ips_reached()
    create_dict["address"] = new_ip_address
    new_db_peer = crud_peer.create(session, obj_in = create_dict)
    set_proc = utils.wg_set_cmd(peer = new_db_peer)
    if set_proc.stderr:
        raise exceptions.server_error("error when trying to add a peer to if")
    return new_db_peer


@peer_router.put(
    "/peer/{peer_id}",
    response_model = DBPlusStdoutPeer,
    dependencies = [Depends(get_current_active_superuser)],
)
async def update_peer(
        peer_id: uuid.UUID,
        peer: PeerUpdate,
        session: SessionDep
) -> DBPlusStdoutPeer:
    db_peer = session.get(Peer, peer_id)
    updated_peer_dict = peer.model_dump(exclude_none = True, exclude_unset = True, exclude = {"preshared_key"})
    # updated_peer_dict['allowedIPs'] = ",".join(peer.allowedIPs)
    updated_peer = crud_peer.update(session, db_obj = db_peer, obj_in = updated_peer_dict)
    if not updated_peer.enabled:
        utils.wg_set_rm_cmd(updated_peer)
    return updated_peer


@peer_router.delete(
    "/peer/{peer_id}",
    response_model = DbDataPeer,
    dependencies = [Depends(get_current_active_superuser)],
)
async def delete_peer(
        peer_id: uuid.UUID,
        session: SessionDep
) -> DbDataPeer:
    deleted_peer = crud_peer.remove(session = session, item_id = peer_id)
    utils.wg_set_rm_cmd(deleted_peer)
    return deleted_peer


@peer_router.get("/peer/{peer_id}/configuration", dependencies = [Depends(get_current_active_superuser)])
async def peer_configuration(
        peer_id: uuid.UUID,
        session: SessionDep
):
    stmt = select(
        Peer.name,
        Peer.private_key,
        Peer.preshared_key,
        Peer.if_public_key,
        Peer.address,
        Peer.allowed_ips,
        Peer.persistent_keepalive
    ).where(Peer.id == peer_id)
    peer = session.execute(stmt).first()
    if not peer:
        raise exceptions.peer_not_found()
    peer_config = crud_peer.get_peer_config(peer)
    file_name = re.sub("[^a-zA-Z0-9_=+.-]", "-", peer.name)
    file_name = re.sub("(-{2,}|-)", "-", file_name)
    file_name = re.sub("(-)", "", file_name)[:32]
    f = StringIO(peer_config)
    headers = {
        "Content-Disposition": f"attachment; filename={file_name}.conf",
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Length": str(len(f.getvalue())),
    }
    return StreamingResponse(f, headers = headers)


@peer_router.get(
    "/peer/{peer_id}/svgqrcode",
    dependencies = [Depends(get_current_active_superuser)]
)
async def create_svg_from_config(
        peer_id: uuid.UUID,
        session: SessionDep
):
    stmt = select(
        Peer.name,
        Peer.private_key,
        Peer.preshared_key,
        Peer.if_public_key,
        Peer.address,
        Peer.allowed_ips,
        Peer.persistent_keepalive
    ).where(Peer.id == peer_id)
    peer = session.execute(stmt).first()
    if not peer:
        raise exceptions.peer_not_found()
    svg = crud_peer.peer_qrcode_svg(peer)
    return Response(
        svg.to_string(),
        headers = {
            "Content-Type": "image/svg+xml; charset=utf-8"
        }
    )
