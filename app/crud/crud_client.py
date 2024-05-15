import qrcode, uuid
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.wgserver import WGServer
from app.schemas.client import ClientCreate, ClientUpdate
from app.models.client import Client
from app.core.Settings import get_settings
import subprocess, os, datetime, logging, qrcode, uuid
from qrcode.image.svg import SvgPathImage
from app.crud.crud_wgserver import crud_wgserver

settings = get_settings()
logging.basicConfig(level=logging.INFO)


class CRUDClient(CRUDBase[Client, ClientCreate, ClientUpdate]):
    def create(self, db: Session, *, obj_in: ClientCreate, server: WGServer) -> Client:
        new_ip_address = None
        clients = db.query(Client).all()
        clients_len = db.query(Client).count()
        if clients_len == 0:
            new_ip_address = settings.WG_DEFAULT_ADDRESS.replace("x", str(2))
        else:
            for i in range(2, 255):
                ip_available = False
                for client in clients:
                    if client.address == settings.WG_DEFAULT_ADDRESS.replace(
                        "x", str(i)
                    ):
                        ip_available = True
                if not ip_available:
                    new_ip_address = settings.WG_DEFAULT_ADDRESS.replace("x", str(i))
                    break

        if not new_ip_address:
            raise Exception("Maximum number of clients reached.")
        new_client = Client(
            name=obj_in.name,
            enabled=obj_in.enabled,
            address=new_ip_address,
            publicKey=obj_in.publicKey,
            privateKey=obj_in.privateKey,
            preSharedKey=obj_in.preSharedKey,
            persistentKeepalive=25,
            allowedIPs="0.0.0.0/0,::/0",
            wgserver_id=server.id,
        )
        return self.save(db, new_client)

    def client_list_out(self, session: Session) -> list[Client]:
        orm_client_list = session.query(self.model).all()
        dump = (
            subprocess.run(
                ["wg", "show", settings.WG_INTERFACE, "dump"], stdout=subprocess.PIPE
            )
            .stdout.decode()
            .strip()
            .splitlines()
        )
        if len(dump):
            # print('-->',orm_client_list[0])
            del dump[0]
        # del dump[0]
        for line in dump:
            (
                publicKey,
                pre_shared_key,
                endpoint,
                address,
                latestHandshakeAt,
                transferRx,
                transferTx,
                persistentKeepalive,
            ) = line.split("\t")
            for client in orm_client_list:
                if client.publicKey == publicKey:
                    if latestHandshakeAt != "0":
                        client.latestHandshakeAt = datetime.datetime.fromtimestamp(
                            int(latestHandshakeAt)
                        )
                    else:
                        client.latestHandshakeAt = None
                    client.persistentKeepalive = (
                        persistentKeepalive if persistentKeepalive != "off" else None
                    )
                    client.transferRx = int(transferRx or 0)
                    client.transferTx = int(transferTx or 0)
                    client.address = address
        session.add_all(orm_client_list)
        return orm_client_list

    def client_qrcode_svg(self, db: Session, client_id: uuid.UUID):
        client_config = self.get_client_config(db, client_id=client_id)
        return qrcode.make(client_config, image_factory=SvgPathImage, box_size=88)

    def get_client_config(self, db: Session, client_id: uuid.UUID):
        client = db.get(self.model, client_id)
        server_public_key = crud_wgserver.get_server_config(session=db).publicKey
        result = [f"{os.linesep}[Interface]", f"Address = {client.address}/24"]
        if client.privateKey:
            result.append(f"PrivateKey = {client.privateKey}")
        if settings.WG_DEFAULT_DNS:
            result.append(f"DNS = {settings.WG_DEFAULT_DNS}")
        if settings.WG_MTU:
            result.append(f"MTU = {settings.WG_MTU}")
        result.append(f"{os.linesep}[Peer]")
        result.append(f"PublicKey = {server_public_key}")
        if client.preSharedKey:
            result.append(f"PresharedKey = {client.preSharedKey}")
        result.append(f"AllowedIPs = 0.0.0.0/0, ::/0")
        result.append(f"PersistentKeepalive = {settings.WG_PERSISTENT_KEEPALIVE}")
        result.append(f"Endpoint = {settings.WG_HOST_IP}:{settings.WG_HOST_PORT}")
        return os.linesep.join(result)


crud_client = CRUDClient(Client)
