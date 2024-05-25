from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from wg_backend.db.registry import DateMixin, NameMixin, mapper_registry


@mapper_registry.mapped
class WGInterface(DateMixin, NameMixin):
    private_key = Column(String(255), nullable = False)
    public_key = Column(String(255), nullable = True)
    address = Column(String(255), nullable = False)
    port = Column(Integer, nullable = False)
    interface = Column(String(50), nullable = False)
    mtu = Column(Integer, nullable = True)
    peers = relationship(
        "Peer",
        back_populates = "wg_interface",
        single_parent = True,
        cascade = "all, delete, delete-orphan",
        # passive_deletes=True,
    )
