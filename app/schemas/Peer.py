import uuid, datetime, subprocess
from pydantic import BaseModel, model_validator
from typing import Optional
# from app.core.Settings import get_settings
#
# settings = get_settings()


class PeerBase(BaseModel):
    mtu: Optional[int] = None
    persistent_keepalive: Optional[int] = None
    rx_bytes: Optional[int] = 0
    tx_bytes: Optional[int] = 0
    last_handshake_time: Optional[datetime.datetime] = None
    fwmark: Optional[int] = None
    enabled: Optional[bool] = None
    endpoint_addr: Optional[str] = None
    endpoint_port: Optional[int] = None
    address: Optional[str] = None
    allowed_ips: Optional[list[str]] = None
    name: Optional[str] = None
    downloadable_config: Optional[bool] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    preshared_key: Optional[str] = None
    
    @model_validator(mode="after")
    def check_transferRx(self):
        if self.rx_bytes is None or not isinstance(self.rx_bytes, int):
            self.rx_bytes = 0
        if self.tx_bytes is None or not isinstance(self.tx_bytes, int):
            self.tx_bytes = 0
        return self
    
    class Config:
        from_attributes = True
    
    
class InterfacePeer(PeerBase):
    public_key: str
    preshared_key: str


class PeerInDbBase(PeerBase):
    id: uuid.UUID
    name: str
    interface_id: int
    private_key: str
    public_key: str
    preshared_key: Optional[str] = None
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None
    enable: Optional[bool] = True
    protocol_version: Optional[str] = None

        
class PeerOut(PeerInDbBase):
    downloadable_config: bool = False
    allowed_ips: Optional[list[str]] = ["0.0.0.0/0, ::/0"]
    persistent_keepalive: Optional[int] = None
    rx_bytes: Optional[int] = 0
    tx_bytes: Optional[int] = 0
    last_handshake_time: Optional[datetime.datetime] = None

    
class PeerUpdate(PeerBase):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    
    @model_validator(mode="after")
    def check_downloadable_config(self):
        if self.private_key:
            self.downloadable_config = True
        return self


class PeerCreate(PeerBase):
    name: str
    interface_id:Optional[int] = None
    
    @model_validator(mode="after")
    def verify_fields(self):
        self.enabled = True
        command = ["wg", "pubkey"]
        self.private_key = (
            subprocess.run(["wg", "genkey"], stdout=subprocess.PIPE)
            .stdout.decode()
            .strip()
        )
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # executable='/bin/bash'
        )
        (stdoutData, stderrData) = proc.communicate(bytes(self.private_key, "utf-8"))
        self.public_key = stdoutData.decode().strip()
        self.preshared_key = (
            subprocess.run(
                ["wg", "genpsk"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # executable='/bin/bash'
            )
            .stdout.decode()
            .strip()
        )
        return self
        
        
class InterfaceConfigOut(PeerBase):
    listen_port: int
    fwmark: Optional[int] = None
    interface_index: int
    interface: str
    private_key: str
    public_key: str
    peers: list[InterfacePeer]
    

class PeerRXRT(BaseModel):
    transfer_rx: int
    transfer_tx: int
    public_key: str


    
    