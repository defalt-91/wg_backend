import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel, TIMESTAMP
from wg_backend.models.wg_interface import WGInterface


class Peer(SQLModel, table = True):
    id: uuid.UUID = Field(default = uuid.uuid4, primary_key = True, index = True, unique = True)
    name: str = Field(max_length = 255)
    enabled: bool
    persistent_keepalive: int = Field(default = 0)
    allowed_ips: str | None = Field(max_length = 255, default = None)
    preshared_key: str | None = Field(max_length = 255, default = None)
    private_key: str = Field(max_length = 255)
    public_key: str = Field(max_length = 255)
    if_public_key: str = Field(max_length = 255)
    address: str = Field(max_length = 255)
    transfer_rx: int = Field(default = 0)
    transfer_tx: int = Field(default = 0)
    last_handshake_at: datetime | None = Field(TIMESTAMP(timezone = True))
    endpoint_addr: str | None = Field(max_length = 255, default = None)
    friendly_name: str | None = Field(max_length = 255, default = None)
    friendly_json: str | None = Field(default = None, max_length = 255)
    interface_id: int = Field(foreign_key = 'wginterface.id')
    wg_interface: WGInterface = Relationship(back_populates = "peers")
