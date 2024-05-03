from app import  models
import uuid
from app.crud.crud_client import crud_client
from app.api import deps
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse,Response
from app.models.client import Client
from app.schemas.client import ClientCreate,ClientsRxTx,ClientOut,ClientUpdate
from app.crud.crud_wgserver import crud_wgserver
from sqlalchemy.orm import Session
from .client_utils import ClientService
from app.api.deps import get_session
from io import StringIO


router = APIRouter()

# client_service = ClientService()

@router.get('/clients',response_model=list[ClientOut])
async def Client_list(
    db: Session = Depends(get_session),
    current_user: models.User = Depends(deps.get_current_active_user),

):
    # clients = client_service.get_clients()
    # return client_service.add_config_to_clients(clients)
    return crud_client.client_list_out(session=db)

@router.post('/client/',response_model=ClientOut)
async def create_client(
        client_in:ClientCreate,
        db: Session = Depends(get_session),
    ):
    # new_client = client_service.createClient(client_in.name)
    # return client_service.getClient(new_client['id'])
    return crud_client.create(db,obj_in=client_in,server=crud_wgserver.get_server_config(db))


@router.put('/client/{client_id}')
async def update_client(client_id:uuid.UUID,client:ClientUpdate,db:Session=Depends(get_session)):
    # client_service.update_client(client=client)
    db_client = db.get(Client,client_id)
    return crud_client.update(db,db_obj=db_client,obj_in=client)


@router.delete('/client/{client_id}')
async def delete_client(client_id:uuid.UUID,db:Session=Depends(get_session)):
    # deleted_user = client_service.deleteClient(client_id)
    deleted_client = crud_client.remove(db=db,id=client_id)
    return deleted_client

@router.get('/client/{client_id}/svgqrcode')
async def create_svg_from_config(client_id:uuid.UUID,db:Session = Depends(get_session)):
    from qrcode.image.svg import SvgImage
    # svg:SvgImage = client_service.getClientQRCodeSVG(clientId=client_id)
    svg:SvgImage = crud_client.client_qrconde_svg(db=db,client_id=client_id)
    return Response(
        svg.to_string(),
        headers={"Content-Type" : "image/svg+xml; charset=utf-8"}
        )

@router.get('/client/{client_id}/configuration')
async def client_configuration(client_id:uuid.UUID,db:Session = Depends(get_session)):
    import re
    # client_config = client_service.getClientConfiguration(client_id)
    client_config = crud_client.getClientConfiguration(db,client_id)
    # client:ClientFromWG = client_service.getClient(clientId=client_id)
    client = crud_client.get(db,client_id)
    client_name = str(client.name)
    file_name=re.sub('[^a-zA-Z0-9_=+.-]','-',client_name)
    file_name=re.sub('(-{2,}|-)','-',file_name)
    file_name=re.sub('(-)','',file_name)[:32]
    f = StringIO(client_config)
    headers={
        'Content-Disposition':f"attachment; filename={file_name}.conf",
        'Content-Length': str(len(f.getvalue()))
        }
    return StreamingResponse(f,headers=headers)

@router.get('/clients/rxrt',response_model=list[ClientsRxTx],response_model_exclude_none=False)
async def clients_rx_rt(db:Session = Depends(get_session)):
    # clients = client_service.get_clients()
    # clients_list = client_service.add_config_to_clients(clients)
    clients_list = crud_client.client_list_out(db)
    # clients_list = [ClientsRxTx(id=c.id,transferRx=c.transferRx,transferTx=c.transferTx) for c in clients_list]
    return clients_list

