import uuid
from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, Uuid, ForeignKey
from sqlalchemy.orm import relationship
from app.db.registry import DateMixin, NameMixin, mapper_registry


@mapper_registry.mapped
class Peer(DateMixin, NameMixin):
    id = Column(Uuid(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True, unique=True)
    name = Column(String(256), index=True)
    enabled = Column(Boolean(), nullable=False)
    interface_id = Column(Integer, ForeignKey("wginterface.id", ondelete="CASCADE"), nullable=False)
    private_key = Column(String(256), nullable=False)
    public_key = Column(String(256), nullable=False)
    preshared_key = Column(String(256), nullable=False)
    address = Column(String(256), nullable=False)
    persistent_keepalive = Column(Integer, nullable=True)
    transfer_rx = Column(Integer, nullable=False, default=lambda: 0)
    transfer_tx = Column(Integer, nullable=False, default=lambda: 0)
    last_handshake_at = Column(TIMESTAMP(timezone=True), index=True, nullable=True, doc="Last hand shake at")
    endpoint_addr = Column(String(256), nullable=True)
    """ this is for peer side tunnel, all traffic option """
    # allowedIPs = Column(String(255), nullable=True)
    friendly_name = Column(String(255), nullable=True)
    friendly_json = Column(String(255), nullable=True)
    wg_interface = relationship(
        "WGInterface",
        back_populates="peers",
    )
