import datetime
import subprocess
import uuid

from pydantic import BaseModel, model_validator


class PeerBase(BaseModel):
    mtu: int | None = None
    persistent_keepalive: int | None = None
    rx_bytes: int | None = 0
    tx_bytes: int | None = 0
    last_handshake_at: datetime.datetime | None = None
    fwmark: int | None = None
    enabled: bool | None = None
    endpoint_addr: str | None = None
    endpoint_port: int | None = None
    address: str | None = None
    allowed_ips: list[str] | None = None
    name: str | None = None
    downloadable_config: bool | None = None
    private_key: str | None = None
    public_key: str | None = None
    preshared_key: str | None = None

    @model_validator(mode="after")
    def check_transferRx(self):
        if self.rx_bytes is None or not isinstance(self.rx_bytes, int):
            self.rx_bytes = 0
        if self.tx_bytes is None or not isinstance(self.tx_bytes, int):
            self.tx_bytes = 0
        return self


class PeerUpdate(PeerBase):
    name: str | None = None
    enabled: bool | None = None


class PeerCreate(PeerBase):
    name: str
    interface_id: int | None = None

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


class PeerInDbBase(BaseModel):
    id: uuid.UUID
    name: str
    enabled: bool | None = None
    interface_id: int
    private_key: str
    public_key: str
    preshared_key: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None
    address: str | None = None
    persistent_keepalive: int | None = None
    transfer_rx: int | None = None
    transfer_tx: int | None = None
    last_handshake_at: datetime.datetime | None = None
    friendly_name: str | None = None
    friendly_json: dict | None = None

    # wg_interface: InterfacePeer | None = None

    class Config:
        # orm_mode = True
        from_attributes = True


class PeerOut(BaseModel):
    id: uuid.UUID
    name: str
    enabled: bool | None = None
    public_key: str
    downloadable_config: bool = False
    # allowed_ips: list[str] | None = ["0.0.0.0/0, ::0"]
    interface_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None
    address: str | None = None
    persistent_keepalive: int | None = None
    transfer_rx: int | None = None
    transfer_tx: int | None = None
    last_handshake_at: datetime.datetime | None = None
    friendly_name: str | None = None
    friendly_json: dict | None = None

    @model_validator(mode="after")
    def check_downloadable_config(self):
        if self.public_key:
            self.downloadable_config = True
        return self


class PeerRXRT(BaseModel):
    public_key: str | None = None
    rx_bytes: int
    tx_bytes: int
    last_handshake_at: datetime.datetime
