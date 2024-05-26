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
from wg_backend.models.wg_interface import WGInterface
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
    return crud_wg_interface.get_rxtx_lha_config()


@peer_router.get(
    "/peers",
    dependencies = [Depends(get_current_active_superuser)],
    response_model = list[DBPlusStdoutPeer],
    response_model_exclude_none = True,
    response_model_exclude_unset = True,
    # response_model_exclude = {},
)
async def peer_list(session: SessionDep):
    """ Peers list """
    stmt = select(Peer.id, Peer.public_key, Peer.name, Peer.enabled, Peer.created_at, Peer.updated_at)
    peers_db_data = session.execute(stmt).fetchall()
    dump_result = utils.get_wg_dump_data()
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
):
    """ Create Wireguard interface peer """
    interface = crud_wg_interface.get_if_db(session, interface_id = interface_id)
    new_schema_peer: PeerCreateForInterface = PeerCreateForInterface.create_from_if(
        db_if = interface,
        peer_in = peer_in
    )
    create_dict = new_schema_peer.model_dump()
    if not preshared_key:
        del create_dict['preshared_key']
    new_db_peer = crud_peer.create(session, obj_in = create_dict)
    # peers = interface.peers
    # if len(peers) >= 1:
    peers = crud_wg_interface.create_write_peers_config_file(peers = interface.peers)
    res = utils.wg_add_conf_cmd(peers)
    if res.stderr:
        raise exceptions.server_error(f"Error when trying to create_peer with addconf to wg. {res.stderr}")
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
):
    db_peer = session.get(Peer, peer_id)
    updated_peer_dict = peer.model_dump(exclude_none = True, exclude_unset = True,exclude = {"preshared_key"})
    # updated_peer_dict['allowedIPs'] = ",".join(peer.allowedIPs)
    updated_peer = crud_peer.update(session, db_obj = db_peer, obj_in = updated_peer_dict)
    if not updated_peer.enabled:
        utils.wg_set_cmd(updated_peer)
    else:
        peers = session.query(WGInterface).one().peers
        crud_wg_interface.create_write_peers_config_file(peers = peers)
        res = utils.wg_add_conf_cmd(peers)
        if res.stderr:
            raise exceptions.server_error(f"Error when trying to update peer with addconf to wg.{res.stderr}")
    return updated_peer


@peer_router.delete(
    "/peer/{peer_id}",
    response_model = DbDataPeer,
    dependencies = [Depends(get_current_active_superuser)],
)
async def delete_peer(peer_id: uuid.UUID, session: SessionDep):
    deleted_peer = crud_peer.remove(session = session, item_id = peer_id)
    utils.wg_set_cmd(deleted_peer)
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
