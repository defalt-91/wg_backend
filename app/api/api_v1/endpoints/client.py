import uuid, re
from app.crud.crud_client import crud_client
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
from app.api.deps import ConnectionManager
from app.models.peer import Peer
from app.schemas.Peer import PeerOut, PeerUpdate, PeerCreate
from app.crud.crud_wgserver import crud_wg_interface
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_superuser, get_session
from io import StringIO

router = APIRouter()
rx_rt_manager = ConnectionManager()


@router.websocket("/ws/rxrt/")
async def websocket_rx_rt(websocket: WebSocket):
	await rx_rt_manager.connect(websocket)
	try:
		while True:
			data = await crud_wg_interface.get_rxrt()
			# msg = await websocket.receive()
			# await rx_rt_manager.broadcast(data)
			await rx_rt_manager.send_personal_message(data=data, websocket=websocket)
	except WebSocketDisconnect:
		rx_rt_manager.disconnect(websocket)
	# await rx_rt_manager.broadcast(f"Peer #{'user_id'} left the chat")


@router.get(
	"/peers",
	response_model=list[PeerOut],
	dependencies=[Depends(get_current_active_superuser)],
)
async def client_list(db: Session = Depends(get_session)):
	# return crud_client.client_list_out(session=db)
	return crud_wg_interface.get_config(db)
	# return crud_client.get_multi(db)


@router.post(
	"/peer/",
	response_model=PeerOut,
	dependencies=[Depends(get_current_active_superuser)],
)
async def create_client(
		client_in: PeerCreate,
		db: Session = Depends(get_session),
):
	server = crud_wg_interface.get_server_config(db)
	client_in.interface_id = server.id
	new_db_peer = crud_client.create(db, obj_in=client_in)
	crud_wg_interface.add_peer(peer=new_db_peer)
	return new_db_peer


@router.put(
	"/peer/{peer_id}",
	response_model=PeerOut,
	dependencies=[Depends(get_current_active_superuser)],
)
async def update_client(
		peer_id: uuid.UUID, client: PeerUpdate, db: Session = Depends(get_session)
):
	db_client = db.get(Peer, peer_id)
	updated_client_dict = client.model_dump(exclude_none=True,exclude_unset=True)
	# updated_client_dict['allowedIPs'] = ",".join(client.allowedIPs)
	updated_client = crud_client.update(db, db_obj=db_client, obj_in=updated_client_dict)
	if not client.enabled:
		crud_wg_interface.remove_peer(client.public_key)
	else:
		crud_wg_interface.update_peer(updated_client)
	return updated_client


@router.delete(
	"/peer/{peer_id}",
	response_model=PeerOut,
	dependencies=[Depends(get_current_active_superuser)],
)
async def delete_client(peer_id: uuid.UUID, db: Session = Depends(get_session)):
	deleted_client = crud_client.remove(db=db, id=peer_id)
	crud_wg_interface.remove_peer(deleted_client.public_key)
	return deleted_client


@router.get(
	"/peer/{peer_id}/svgqrcode",
	dependencies=[Depends(get_current_active_superuser)],
)
async def create_svg_from_config(
		peer_id: uuid.UUID, db: Session = Depends(get_session)
):
	svg = crud_client.client_qrcode_svg(db=db, peer_id=peer_id)
	return Response(
		svg.to_string(), headers={"Content-Type": "image/svg+xml; charset=utf-8"}
	)


@router.get(
	"/peer/{peer_id}/configuration",
	dependencies=[Depends(get_current_active_superuser)],
)
async def client_configuration(
		peer_id: uuid.UUID, db: Session = Depends(get_session)
):
	client_config = crud_client.get_client_config(db, peer_id)
	client = crud_client.get(db, peer_id)
	client_name = str(client.name)
	file_name = re.sub("[^a-zA-Z0-9_=+.-]", "-", client_name)
	file_name = re.sub("(-{2,}|-)", "-", file_name)
	file_name = re.sub("(-)", "", file_name)[:32]
	f = StringIO(client_config)
	headers = {
		"Content-Disposition": f"attachment; filename={file_name}.conf",
		"Content-Type": "text/plain; charset=utf-8",
		"Content-Length": str(len(f.getvalue())),
	}
	return StreamingResponse(f, headers=headers)

# @router.get('/peers/rxrt',response_model=list[PeerRXRT],dependencies=[Depends(get_current_active_superuser)])
# async def clients_rx_rt(db:Session = Depends(get_session)):
#     return crud_client.client_list_out(db)
