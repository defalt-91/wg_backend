# from segno import QRCode
from app import models
import uuid, re, os
from app.crud.crud_client import crud_client
from app.api import deps
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
from app.api.deps import ConnectionManager
from app.models.client import Client
from app.schemas.Peer import PeerRXRT, WireguardConfigOut
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.crud.crud_wgserver import crud_wgserver
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_superuser, get_session
from io import StringIO

router = APIRouter()
rx_rt_manager = ConnectionManager()


@router.websocket("/ws/rxrt/")
async def websocket_rxrt(websocket: WebSocket):
	await rx_rt_manager.connect(websocket)
	try:
		while True:
			data = await crud_wgserver.get_rxrt()
			msg = await websocket.receive_json()
			# await rx_rt_manager.broadcast(data)
			await rx_rt_manager.send_personal_message(data=data, websocket=websocket)
	except WebSocketDisconnect:
		rx_rt_manager.disconnect(websocket)
	# await rx_rt_manager.broadcast(f"Client #{'user_id'} left the chat")


@router.get(
	"/clients",
	response_model=list[ClientOut],
	dependencies=[Depends(get_current_active_superuser)],
)
async def client_list(db: Session = Depends(get_session)):
	# return crud_client.client_list_out(session=db)
	print()
	return crud_wgserver.get_config(db)
	# return crud_client.get_multi(db)


@router.post(
	"/client/",
	response_model=ClientOut,
	dependencies=[Depends(get_current_active_superuser)],
)
async def create_client(
		client_in: ClientCreate,
		db: Session = Depends(get_session),
):
	server = crud_wgserver.get_server_config(db)
	new_db_peer = crud_client.create(db, obj_in=client_in, server=server)
	crud_wgserver.add_peer(client=new_db_peer)
	return new_db_peer


@router.put(
	"/client/{client_id}",
	response_model=ClientOut,
	dependencies=[Depends(get_current_active_superuser)],
)
async def update_client(
		client_id: uuid.UUID, client: ClientUpdate, db: Session = Depends(get_session)
):
	db_client = db.get(Client, client_id)
	updated_client_dict = client.model_dump(exclude_none=True,exclude_unset=True)
	updated_client_dict['allowedIPs'] = ",".join(client.allowedIPs)
	updated_client = crud_client.update(db, db_obj=db_client, obj_in=updated_client_dict)
	if not client.enabled:
		crud_wgserver.remove_peer(client.publicKey)
	else:
		crud_wgserver.update_peer(updated_client)
	return updated_client


@router.delete(
	"/client/{client_id}",
	response_model=ClientOut,
	dependencies=[Depends(get_current_active_superuser)],
)
async def delete_client(client_id: uuid.UUID, db: Session = Depends(get_session)):
	deleted_client = crud_client.remove(db=db, id=client_id)
	crud_wgserver.remove_peer(deleted_client.publicKey)
	return deleted_client


@router.get(
	"/client/{client_id}/svgqrcode",
	dependencies=[Depends(get_current_active_superuser)],
)
async def create_svg_from_config(
		client_id: uuid.UUID, db: Session = Depends(get_session)
):
	svg = crud_client.client_qrcode_svg(db=db, client_id=client_id)
	return Response(
		svg.to_string(), headers={"Content-Type": "image/svg+xml; charset=utf-8"}
	)


@router.get(
	"/client/{client_id}/configuration",
	dependencies=[Depends(get_current_active_superuser)],
)
async def client_configuration(
		client_id: uuid.UUID, db: Session = Depends(get_session)
):
	client_config = crud_client.get_client_config(db, client_id)
	client = crud_client.get(db, client_id)
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

# @router.get('/clients/rxrt',response_model=list[PeerRXRT],dependencies=[Depends(get_current_active_superuser)])
# async def clients_rx_rt(db:Session = Depends(get_session)):
#     return crud_client.client_list_out(db)
