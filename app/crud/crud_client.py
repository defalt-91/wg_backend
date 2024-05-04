import qrcode
import uuid
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.wgserver import WGServer
from app.schemas.client import ClientCreate,ClientUpdate
from app.models.client import Client
from app.core.Settings import get_settings
import subprocess
import logging
import datetime

settings = get_settings()
logging.basicConfig(level=logging.INFO)

class CRUDClient(CRUDBase[Client, ClientCreate, ClientUpdate]):
    def create(self, db: Session, *, obj_in: ClientCreate,server:WGServer) -> Client:
        new_ip_address=None
        clients = db.query(Client).all()
        clients_len = db.query(Client).count()
        if clients_len == 0:
            new_ip_address = settings.WG_DEFAULT_ADDRESS.replace('x', str(2))
        else:
            for i in range(2,255):
                ip_available = False
                for client in clients:
                    if client.address == settings.WG_DEFAULT_ADDRESS.replace('x', str(i)):
                        ip_available = True
                if not ip_available:
                    new_ip_address = settings.WG_DEFAULT_ADDRESS.replace('x', str(i))
                    break
        
        if not new_ip_address:
            raise Exception('Maximum number of clients reached.')
        new_client = Client(
            name = obj_in.name,
            enabled = obj_in.enabled,
            address = new_ip_address,
            publicKey = obj_in.publicKey,
            privateKey = obj_in.privateKey,
            preSharedKey = obj_in.preSharedKey,
            wgserver_id = server.id
        )
        db_client=self.save(db,new_client)
        # self.save_and_sync_wg_config(db=db)
        return db_client
    def client_list_out(self,session:Session)->list[Client]:
        orm_client_list = session.query(self.model).all()
        dump = subprocess.run(["wg", "show" ,"wg0", "dump"],stdout=subprocess.PIPE).stdout.decode().strip().splitlines()
        # if len(dump):
            # del dump[0]
        del dump[0]
        for line in dump :
            (
                publicKey,
                pre_shared_key,
                endpoint,
                allowedIps,
                latestHandshakeAt,
                transferRx,
                transferTx,
                persistentKeepalive
             ) = line.split('\t')
            for client in orm_client_list:
                if client.publicKey == publicKey:
                    if latestHandshakeAt != '0':
                        client.latestHandshakeAt = datetime.fromtimestamp(int(latestHandshakeAt))
                    else:
                        client.latestHandshakeAt = None
                    client.persistentKeepalive = persistentKeepalive
                    client.transferRx = int(transferRx or 0)    
                    client.transferTx = int(transferTx or 0)
                    client.allowedIPs=allowedIps
        session.add_all(orm_client_list)
        return orm_client_list
    def client_qrconde_svg(self,db:Session,client_id:uuid.UUID):
        client_config = self.getClientConfiguration(db,client_id=client_id)
        method = "fragment"
        if method == 'basic':
            # Simple factory, just a set of rects.
            factory = qrcode.image.svg.SvgImage
        elif method == 'fragment':
            # Fragment factory (also just a set of rects)
            factory = qrcode.image.svg.SvgFragmentImage
        elif method == 'path':
            # Combined path factory, fixes white space that may occur when zooming
            factory = qrcode.image.svg.SvgPathImage
        sqvqrcode = qrcode.make(client_config,
                                image_factory=factory,
                                box_size=22
                                )
        # qrcode.save('file.svg')
        return sqvqrcode
    def getClientConfiguration(self,db:Session, client_id:uuid.UUID ) :
        client = db.get(self.model,client_id)
        server_public_key = db.query(WGServer).first().publicKey
        priv_key = 'REPLACE_ME'
        if client.privateKey:
            priv_key=client.privateKey
        defautl_dns = ''
        if settings.WG_DEFAULT_DNS:
            defautl_dns = f"DNS = {settings.WG_DEFAULT_DNS}\n"
        wg_mtu_str = ''
        if settings.WG_MTU:
            wg_mtu_str = f"MTU = {settings.WG_MTU}\n"
        pre_shared_key_str=''
        if client.preSharedKey:
            pre_shared_key_str=f"PresharedKey = {client.preSharedKey}\n"
        return f"""
[Interface]
PrivateKey = {priv_key}
Address = {client.address}/24
{defautl_dns}\
{wg_mtu_str}\

[Peer]
PublicKey = {server_public_key}
{pre_shared_key_str}
AllowedIPs = {settings.WG_ALLOWED_IPS}
PersistentKeepalive = {settings.WG_PERSISTENT_KEEPALIVE}
Endpoint = {settings.WG_HOST}:{settings.WG_PORT}"""

    # def get_config(self,session:Session,server:WGServerInDB) -> dict:
    #     server_in = session.query(WGServer).first()
    #     client_list = session.query(self.model).all()
    #     # (Client).order_by(-Client.updated_at)
    #     # returned_tuple = session.execute(statement)
    #     # client_list = returned_tuple.scalars().all()
    #     self.__save_wgserver_dot_conf(client_list)
    #     return 

crud_client = CRUDClient(Client)