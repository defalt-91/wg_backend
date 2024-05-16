from typing import Type
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.peer import Peer
from app.models.wg_interface import WGInterface
from app.schemas.Peer import PeerRXRT, InterfaceConfigOut,InterfacePeer
from app.schemas.wg_interface import WGInterfaceCreate, WGInterfaceUpdate
from app.core.Settings import get_settings
import datetime, os, logging, pyroute2, subprocess

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CRUDWGServer(CRUDBase[WGInterface, WGInterfaceCreate, WGInterfaceUpdate]):
    def __init__(self, model: WGInterface):
        self.wg = pyroute2.WireGuard()
        super().__init__(model)

    def get_server_config(self, session: Session) -> Type[WGInterface] | None:
        return session.query(self.model).first()

    def create_write_wgserver_file(self, orm_server: WGInterface):
        logger.info(
            f"Writing database server config file to: {settings.wgserver_file_path}"
        )
        result = []
        result.append("# Note: Do not edit this file directly.")
        result.append(f"# Your changes will be overwritten!{os.linesep}# Server")
        result.append(f"{os.linesep}[Interface]")
        result.append(f"PrivateKey = {orm_server.private_key}")
        result.append(f"Address = {orm_server.address}/24")
        result.append(f"ListenPort = {settings.WG_HOST_PORT}")
        if settings.WG_MTU:
            result.append(f"MTU = {settings.WG_MTU}")
        result.append(f"PreUp = {settings.WG_PRE_UP}")
        result.append(f"PostUp = {settings.WG_POST_UP}")
        result.append(f"PreDown = {settings.WG_PRE_DOWN}")
        result.append(f"PostDown = {settings.WG_POST_DOWN}")
        logger.debug("Server Config saving...")
        with open(file=settings.wgserver_file_path, mode="w+", encoding="utf-8") as f:
            f.write(os.linesep.join(result))
        logger.debug(f"Server Config saved to -->{settings.wgserver_file_path}")
        return result

    def sync_db_peers_to_wg(self, db: Session):
        logger.info("Peers loading from database ...")
        peers = db.query(Peer).all()
        if len(peers):
            for peer in peers:
                self.add_peer(peer)
        logger.debug("Peers synced to wg service.")

    def add_peer(self, peer: Peer):
        logger.debug("adding new peer to wg", peer.id)
        new_peer = self.set_peer_args(peer=peer)
        self.wg.set(
            interface=settings.WG_INTERFACE,
            listen_port=settings.WG_HOST_PORT,
            fwmark=None,
            # private_key=server.privateKey,
            peer=new_peer.model_dump(
                exclude_none=True,
                exclude_unset=True,
                exclude={"endpoint_addr", "endpoint_port"},
            ),
        )

    def remove_peer(self, public_key: str):
        self.wg.set(
            settings.WG_INTERFACE, peer={"public_key": str(public_key), "remove": True}
        )

    def update_peer(self, peer: Peer):
        updated_peer = self.set_peer_args(peer=peer)
        updated_peer_dict = updated_peer.model_dump(
            exclude_none=True,
            exclude_unset=True,
            exclude={"endpoint_addr", "endpoint_port"},
        )
        self.wg.set(
            interface=settings.WG_INTERFACE,
            peer=updated_peer_dict,
        )

    def set_peer_args(self, peer: Peer):
        print("====>address", peer.address)
        # print("allowedIps", client.allowedIPs)
        return InterfacePeer(
            public_key=peer.public_key,
            endpoint_addr=str(settings.WG_HOST_IP),
            endpoint_port=settings.WG_HOST_PORT,
            preshared_key=peer.preshared_key,
            persistent_keepalive=peer.persistent_keepalive,
            address=f"{peer.address}/32",
        )

    async def get_rxrt(self):
        try:
            proc = subprocess.run(
                ["wg", "show", settings.WG_INTERFACE, "transfer"],
                capture_output=True,
                text=True,
            )
            lines = proc.stdout.strip().splitlines()
            peer_rx_rt_list: list[dict[str, str | int]] = []
            for peer in lines:
                public_key, rx, tx = peer.split("\t")
                peer_rx_rt_list.append(
                    PeerRXRT(
                        public_key=public_key, transfer_rx=rx, transfer_tx=tx
                    ).model_dump()
                )
            return      peer_rx_rt_list
        except pyroute2.netlink.exceptions.NetlinkError as exc:
            msg = f"Unable to access interface: {exc.args[1]}"
            raise RuntimeError(msg) from exc

    def get_config(self, db: Session) -> InterfaceConfigOut:
        try:
            attrs = dict(self.wg.info(settings.WG_INTERFACE)[0]["attrs"])
            with open(f"{settings.WG_CONFIG_DIR_PATH}/wg_output_attrs.py", "w+") as f:
                 f.write(attrs.__str__())
        except pyroute2.netlink.exceptions.NetlinkError as exc:
            msg = f"Unable to access interface: {exc.args[1]}"
            raise RuntimeError(msg) from exc
        if_config = InterfaceConfigOut(
            private_key=attrs["WGDEVICE_A_PRIVATE_KEY"].decode("utf-8"),
            fwmark=attrs["WGDEVICE_A_FWMARK"],
            listen_port=attrs["WGDEVICE_A_LISTEN_PORT"] or None,
            interface=attrs["WGDEVICE_A_IFNAME"],
            interface_index=attrs["WGDEVICE_A_IFINDEX"],
            public_key=attrs["WGDEVICE_A_PUBLIC_KEY"],
            peers=[
                InterfacePeer(
                    public_key=peer_attrs["WGPEER_A_PUBLIC_KEY"].decode("utf-8"),
                    preshared_key=peer_attrs["WGPEER_A_PRESHARED_KEY"].decode("utf-8")
                    or None,
                    endpoint_addr=peer_attrs.get("WGPEER_A_ENDPOINT", {}).get(
                        "addr", None
                    ),
                    endpoint_port=peer_attrs.get("WGPEER_A_ENDPOINT", {}).get(
                        "port", None
                    ),
                    persistent_keepalive=peer_attrs[
                        "WGPEER_A_PERSISTENT_KEEPALIVE_INTERVAL"
                    ]
                    or None,
                    allowed_ips=[
                        allowed_ip["addr"]
                        for allowed_ip in peer_attrs.get("WGPEER_A_ALLOWEDIPS", [])
                    ],
                    last_handshake_time=peer_attrs.get(
                        "WGPEER_A_LAST_HANDSHAKE_TIME", {}
                    ).get(
                        "tv_sec",
                    ),
                    rx_bytes=peer_attrs.get("WGPEER_A_RX_BYTES"),
                    tx_bytes=peer_attrs.get("WGPEER_A_TX_BYTES"),
                )
                for peer_attrs in (
                    dict(peer["attrs"]) for peer in attrs.get("WGDEVICE_A_PEERS", [])
                )
            ],
        )
        orm_server: WGInterface = db.query(WGInterface).get(settings.SERVER_ID)
        peers: list[Peer] = orm_server.peers
        for db_peer in peers:
            for interface_peer in if_config.peers:
                if db_peer.public_key == interface_peer.public_key:
                    db_peer.transfer_tx = interface_peer.tx_bytes
                    db_peer.transfer_rx = interface_peer.rx_bytes
                    db_peer.latestHandshakeAt = interface_peer.last_handshake_time
                    # db_peer.persistentKeepalive = interface_peer.persistent_keepalive
                    # enabled
                    db_peer.friendly_name = "friendly_name"
                    # friendly_json={"hello":"world"}
                    db_peer.wgserver_id = orm_server.id
        db.add_all(peers)
        db.commit()
        return peers


crud_wg_interface = CRUDWGServer(WGInterface)
