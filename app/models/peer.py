import uuid
from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, Uuid, ForeignKey
from sqlalchemy.orm import relationship
from app.db.registry import DateMixin, NameMixin, mapper_registry


@mapper_registry.mapped
class Peer(DateMixin, NameMixin):
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
	public_key = Column(String(256), nullable=False)
	private_key = Column(String(256), nullable=False)
	preshared_key = Column(String(256), nullable=False)
	latest_handshake_at = Column(
		TIMESTAMP(timezone=True),
		index=True,
		nullable=True,
		doc="Last hand shake at",
	)
	persistent_keepalive = Column(Integer, nullable=True)
	transfer_rx = Column(Integer, nullable=False, default=lambda: 0)
	transfer_tx = Column(Integer, nullable=False, default=lambda: 0)
	""" this is for peer side tunnel all traffic option """
	# allowedIPs = Column(String(255), nullable=True)
	friendly_name = Column(String(255), nullable=True)
	friendly_json = Column(String(255), nullable=True)
	# interface_id = Column(ForeignKey(WGServer.id, ondelete="CASCADE"), nullable=False)
	interface_id = Column(
		Integer, ForeignKey("wginterface.id", ondelete="CASCADE"), nullable=False
	)
	
	wg_interface = relationship(
		"WGInterface",
		back_populates="peers",
		# order_by="desc(Token.created_at)"
	)
	
	# def __repr__(self):
	#     return f"<{self.__class__.__name__}, id={self.id}>"
	
	# def __str__(self):
	#     return self.__repr__()
	
	# __mapper_args__ = {"always_refresh": True}
