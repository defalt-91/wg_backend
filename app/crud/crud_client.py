from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.schemas.Peer import PeerUpdate,PeerCreate
from app.models.peer import Peer
from app.core.Settings import get_settings
import subprocess, os, datetime, logging, qrcode, uuid
from qrcode.image.svg import SvgPathImage
from app.crud.crud_wgserver import crud_wg_interface

settings = get_settings()
logging.basicConfig(level=logging.INFO)


class CRUDClient(CRUDBase[Peer, PeerCreate, PeerUpdate]):
    def create(self, db: Session, *, obj_in: PeerCreate) -> Peer:
        new_ip_address = None
        clients = db.query(Peer).all()
        clients_len = db.query(Peer).count()
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
        new_client = Peer(
            name=obj_in.name,
            enabled=obj_in.enabled,
            address=new_ip_address,
            public_key=obj_in.public_key,
            private_key=obj_in.private_key,
            preshared_key=obj_in.private_key,
            persistent_keepalive=25,
            # allowedIPs="0.0.0.0/0,::/0",
            interface_id=obj_in.interface_id,
        )
        return self.save(db, new_client)

    def client_list_out(self, session: Session) -> list[Peer]:
        orm_peers = session.query(self.model).all()
        dump = (
            subprocess.run(
                ["wg", "show", settings.WG_INTERFACE, "dump"], stdout=subprocess.PIPE
            )
            .stdout.decode()
            .strip()
            .splitlines()
        )
        if len(dump):
            # print('-->',orm_peers[0])
            del dump[0]
        # del dump[0]
        for line in dump:
            (
                publicKey,
                pre_shared_key,
                endpoint,
                address,
                latestHandshakeAt,
                transfer_rx,
                transfer_tx,
                persistent_keepalive,
            ) = line.split("\t")
            for peer in orm_peers:
                if peer.public_key == public_key:
                    if latestHandshakeAt != "0":
                        peer.latestHandshakeAt = datetime.datetime.fromtimestamp(
                            int(latestHandshakeAt)
                        )
                    else:
                        peer.latestHandshakeAt = None
                    peer.persistent_keepalive = (
                        persistent_keepalive if persistent_keepalive != "off" else None
                    )
                    peer.transferRx = int(transfer_rx or 0)
                    peer.transferTx = int(transfer_tx or 0)
                    peer.address = address
        session.add_all(orm_peers)
        return orm_peers

    def client_qrcode_svg(self, db: Session, peer_id: uuid.UUID):
        client_config = self.get_client_config(db, peer_id=peer_id)
        return qrcode.make(client_config, image_factory=SvgPathImage, box_size=88)

    def get_client_config(self, db: Session, peer_id: uuid.UUID):
        client = db.get(self.model, peer_id)
        server_public_key = crud_wg_interface.get_server_config(session=db).public_key
        result = [f"{os.linesep}[Interface]", f"Address = {client.address}/24"]
        if client.private_key:
            result.append(f"PrivateKey = {client.private_key}")
        if settings.WG_DEFAULT_DNS:
            result.append(f"DNS = {settings.WG_DEFAULT_DNS}")
        if settings.WG_MTU:
            result.append(f"MTU = {settings.WG_MTU}")
        result.append(f"{os.linesep}[Peer]")
        result.append(f"PublicKey = {server_public_key}")
        if client.preshared_key:
            result.append(f"PresharedKey = {client.preshared_key}")
        result.append("AllowedIPs = 0.0.0.0/0, ::/0")
        result.append(f"PersistentKeepalive = {settings.WG_PERSISTENT_KEEPALIVE}")
        result.append(f"Endpoint = {settings.WG_HOST_IP}:{settings.WG_HOST_PORT}")
        return os.linesep.join(result)


crud_client = CRUDClient(Peer)
