import logging
import os
from random import randint

import qrcode
from qrcode.image.svg import SvgPathImage
from sqlalchemy import select
from sqlalchemy.orm import Session
from wg_backend.api import exceptions
from wg_backend.core.settings import get_settings
from wg_backend.crud.base import CRUDBase
from wg_backend.models.peer import Peer
from wg_backend.schemas.Peer import PeerCreate, PeerUpdate


settings = get_settings()
logging.basicConfig(level = settings.LOG_LEVEL)


class CRUDPeer(CRUDBase[Peer, PeerCreate, PeerUpdate]):
    def create(self, session: Session, *, obj_in: dict) -> Peer:
        stmt = select(Peer.address)
        peer_addresses = session.execute(stmt).scalars()
        addresses_set = set(peer_addresses)
        new_ip_address = self.generate_new_address(addresses_set)
        if not new_ip_address:
            raise exceptions.wg_max_num_ips_reached()
        new_peer = Peer(
            **obj_in,
            address = new_ip_address,
        )
        return self.save(session, new_peer)


    def peer_qrcode_svg(self, peer: Peer):
        peer_config = self.get_peer_config(peer)
        return qrcode.make(peer_config, image_factory = SvgPathImage, box_size = 40)

    @staticmethod
    def get_peer_config(peer: Peer):
        (
            _,
            private_key,
            preshared_key,
            if_public_key,
            address,
            allowed_ips,
            persistent_keepalive
        ) = peer
        result: list[str] = []
        result.append(f"{os.linesep}[Interface]")
        result.append(f"Address = {address}/24")
        if private_key:
            result.append(f"PrivateKey = {private_key if private_key else 'REPLACE_ME'}")
        if settings.WG_DEFAULT_DNS:
            result.append(f"DNS = {settings.WG_DEFAULT_DNS}")
        if settings.WG_MTU:
            result.append(f"MTU = {settings.WG_MTU}")
        result.append(f"{os.linesep}[Peer]")
        result.append(f"PublicKey = {if_public_key}")
        if preshared_key:
            result.append(f"PresharedKey = {preshared_key}")
        result.append(f"PersistentKeepalive = {persistent_keepalive}")
        result.append(f"Endpoint = {settings.WG_HOST_IP}:{settings.WG_LISTEN_PORT}")
        result.append(f"AllowedIPs = {allowed_ips if allowed_ips else 'AllowedIPs = 0.0.0.0/0, ::/0'}")
        return os.linesep.join(result)

    @staticmethod
    def generate_new_address(addresses_set: set[str]) -> str | None:
        default_addr = settings.WG_DEFAULT_ADDRESS
        new_address = None
        for i in range(2, 255):
            random_int = randint(2, 255)
            new_address = default_addr.replace("x", str(random_int))
            if new_address not in addresses_set:
                break
        return new_address


crud_peer = CRUDPeer(Peer)
