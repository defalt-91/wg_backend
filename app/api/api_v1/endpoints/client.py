from app import  models
import uuid,re
from app.crud.crud_client import crud_client
from app.api import deps
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse,Response
from app.models.client import Client
from app.schemas.client import ClientCreate,ClientsRxTx,ClientOut,ClientUpdate
from app.crud.crud_wgserver import crud_wgserver
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_superuser, get_session
from io import StringIO


router = APIRouter()

# client_service = ClientService()

@router.get('/clients',response_model=list[ClientOut],dependencies=[Depends(get_current_active_superuser)])
async def Client_list(
    # req:Request,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(deps.get_current_active_user),

):
    # clients = client_service.get_clients()
    # return client_service.add_config_to_clients(clients)
    # print(req.state.wg_server.id)
    return crud_client.client_list_out(session=db)

@router.post('/client/',response_model=ClientOut,dependencies=[Depends(get_current_active_superuser)])
async def create_client(
        client_in:ClientCreate,
        db: Session = Depends(get_session),
    ):
    server = crud_wgserver.get_server_config(db)
    new_peer = crud_client.create(db,obj_in=client_in,server=server)
    crud_wgserver.save_and_sync_wg_peer_config(wgserver=server)
    return new_peer


@router.put('/client/{client_id}',response_model=ClientOut,dependencies=[Depends(get_current_active_superuser)])
async def update_client(client_id:uuid.UUID,client:ClientUpdate,db:Session=Depends(get_session)):
    # client_service.update_client(client=client)
    db_client = db.get(Client,client_id)
    server = crud_wgserver.get_server_config(db)
    updated_client = crud_client.update(db,db_obj=db_client,obj_in=client)
    crud_wgserver.save_and_sync_wg_peer_config(wgserver=server)
    return updated_client


@router.delete('/client/{client_id}',response_model=ClientOut,dependencies=[Depends(get_current_active_superuser)])
async def delete_client(client_id:uuid.UUID,db:Session=Depends(get_session)):
    # deleted_user = client_service.deleteClient(client_id)
    server = crud_wgserver.get_server_config(db)
    deleted_client = crud_client.remove(db=db,id=client_id)
    crud_wgserver.save_and_sync_wg_peer_config(wgserver=server)
    return deleted_client

@router.get('/client/{client_id}/svgqrcode',dependencies=[Depends(get_current_active_superuser)])
async def create_svg_from_config(client_id:uuid.UUID,db:Session = Depends(get_session)):
    from qrcode.image.svg import SvgImage
    # svg:SvgImage = client_service.getClientQRCodeSVG(clientId=client_id)
    svg:SvgImage = crud_client.client_qrconde_svg(db=db,client_id=client_id)
    return Response(
        svg.to_string(),
        headers={"Content-Type" : "image/svg+xml; charset=utf-8"}
        )

@router.get('/client/{client_id}/configuration',dependencies=[Depends(get_current_active_superuser)])
async def client_configuration(client_id:uuid.UUID,db:Session = Depends(get_session)):
    client_config = crud_client.getClientConfiguration(db,client_id)
    client = crud_client.get(db,client_id)
    client_name = str(client.name)
    file_name=re.sub('[^a-zA-Z0-9_=+.-]','-',client_name)
    file_name=re.sub('(-{2,}|-)','-',file_name)
    file_name=re.sub('(-)','',file_name)[:32]
    f = StringIO(client_config)
    headers={
        'Content-Disposition':f"attachment; filename={file_name}.conf",
        "Content-Type":"text/plain; charset=utf-8",
        'Content-Length': str(len(f.getvalue()))
        }
    return StreamingResponse(f,headers=headers)

@router.get('/clients/rxrt',response_model=list[ClientsRxTx],dependencies=[Depends(get_current_active_superuser)])
async def clients_rx_rt(db:Session = Depends(get_session)):
    return crud_client.client_list_out(db)



