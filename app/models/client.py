from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, Uuid, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.db.registry import DateMixin, NameMixin, mapper_registry


@mapper_registry.mapped
class Client(DateMixin, NameMixin):
    id = Column(
        Uuid(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True,
        index=True,
        unique=True,
    )
    name = Column(
        String(256),
        index=True,
    )
    enabled = Column(Boolean(), nullable=False, default=True)
    address = Column(String(256), nullable=False)
    publicKey = Column(String(256), nullable=False)
    privateKey = Column(String(256), nullable=False)
    preSharedKey = Column(String(256), nullable=False)
    latestHandshakeAt = Column(
        TIMESTAMP(timezone=True), index=True, nullable=True, doc="Last hand shake at"
    )
    persistentKeepalive = Column(Integer, nullable=True)
    transferRx = Column(Integer, nullable=False, default=lambda: 0)
    transferTx = Column(Integer, nullable=False, default=lambda: 0)
    allowedIPs = Column(String(255), nullable=True)
    friendly_name = Column(String(255), nullable=True)
    friendly_json = Column(String(255), nullable=True)
    # wgserver_id = Column(ForeignKey(WGServer.id, ondelete="CASCADE"), nullable=False)
    wgserver_id = Column(
        Integer, ForeignKey("wgserver.id", ondelete="CASCADE"), nullable=False
    )

    server = relationship(
        "WGServer",
        back_populates="clients",
        # order_by="desc(Token.created_at)"
    )

    # def __repr__(self):
    #     return f"<{self.__class__.__name__}, id={self.id}>"

    # def __str__(self):
    #     return self.__repr__()

    __mapper_args__ = {"always_refresh": True}
