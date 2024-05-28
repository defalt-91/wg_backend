import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP, Uuid
from sqlalchemy.orm import relationship
from wg_backend.db.registry import DateMixin, NameMixin, mapper_registry
from wg_backend.models.wg_interface import WGInterface


@mapper_registry.mapped
class Peer(DateMixin, NameMixin):
    id = Column(Uuid(as_uuid = True), default = uuid.uuid4, primary_key = True, index = True, unique = True)
    name = Column(String(256), index = True, nullable = False)
    enabled = Column(Boolean(), nullable = False)
    interface_id = Column(Integer, ForeignKey(WGInterface.id, ondelete = "CASCADE"), nullable = False)
    persistent_keepalive = Column(Integer, nullable = True, default = 0)
    allowed_ips = Column(String(255))
    preshared_key = Column(String(256), nullable = True)
    private_key = Column(String(256), nullable = False)
    public_key = Column(String(256), nullable = False)
    if_public_key = Column(String(256), nullable = False, server_default = '')
    address = Column(String(256), nullable = False)
    transfer_rx = Column(Integer, nullable = False, default = 0)
    transfer_tx = Column(Integer, nullable = False, default = 0)
    last_handshake_at = Column(TIMESTAMP(timezone = True), index = True, nullable = True, doc = "Last hand shake at")
    endpoint_addr = Column(String(256), nullable = True)
    """ this is for peer side tunnel, all traffic option """
    friendly_name = Column(String(255), nullable = True)
    friendly_json = Column(String(255), nullable = True)
    wg_interface = relationship(
        WGInterface,
        back_populates = "peers",
    )
