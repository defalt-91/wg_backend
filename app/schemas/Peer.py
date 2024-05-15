import uuid, datetime
from pydantic import BaseModel, IPvAnyAddress
from typing import Optional, Union


class PeerInWireguard(BaseModel):
    public_key: str
    preshared_key: str
    endpoint_addr: Optional[str] = None
    endpoint_port: Optional[int] = None
    last_handshake_time: Optional[int] = None
    persistent_keepalive: Optional[int] = None
    tx_bytes: Optional[int] = None
    rx_bytes: Optional[int] = None
    address: Optional[list[str]] = None
    allowed_ips: Optional[list[str]] = None


    # id: uuid.uuid4
    # name: str
    # wgserver_id: str
    # createdat: datetime.datetime
    # updatedat: Optional[datetime.datetime] = None
    # downloadableConfig: Optional[bool] = True
    # enable: Optional[bool] = True
    # protocol_version:Optional[str]=None

class WireguardConfigOut(BaseModel):
    listen_port: int
    fw_mark: Optional[int] = None
    interface_index: int
    interface: str
    private_key: str
    public_key: str
    peers: list[PeerInWireguard]


class PeerRXRT(BaseModel):
    transferRx: int
    transferTx: int
    public_key: str
