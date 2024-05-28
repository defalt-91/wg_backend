from sqlalchemy.orm import Session
from wg_backend.crud.base import CRUDBase
from wg_backend.models.peer import Peer
from wg_backend.schemas.Peer import PeerCreate, PeerUpdate


class CRUDPeer(CRUDBase[Peer, PeerCreate, PeerUpdate]):
    def create(self, session: Session, *, obj_in: dict) -> Peer:
        return self.save(session, Peer(**obj_in))


crud_peer = CRUDPeer(Peer)
