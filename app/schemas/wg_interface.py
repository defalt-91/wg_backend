import datetime
import subprocess

from pydantic import BaseModel, model_validator

from app.core.Settings import get_settings


settings = get_settings()


class WGInterface(BaseModel):
    interface: str | None = None
    address: str | None = None
    port: int | None = None
    mtu: int | None = None
    private_key: str | None = None
    public_key: str | None = None


class WGInterfaceCreate(WGInterface):
    interface: str

    @model_validator(mode="after")
    def create_server(self):
        private_key = subprocess.run(["wg", "genkey"], capture_output=True).stdout
        public_key = subprocess.run(
            ["wg", "pubkey"],
            input=private_key,
            capture_output=True,
            # executable='/bin/bash'
        ).stdout

        if not self.address:
            self.address = settings.WG_DEFAULT_ADDRESS.replace("x", "1")
        self.private_key = private_key.decode().strip()
        self.public_key = public_key.decode().strip()
        # address = str(settings.WG_HOST_IP),
        self.port = settings.WG_HOST_PORT
        if not self.interface:
            self.interface = settings.WG_INTERFACE
        if settings.WG_MTU:
            self.mtu = settings.WG_MTU
        return self
        # command = ["wg","pubkey"]
        # proc = subprocess.Popen(
        #     command,
        #     stdin=subprocess.PIPE,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        #     # executable='/bin/bash'
        # )
        # private_key = subprocess.run(['wg', 'genkey'],stdout=subprocess.PIPE).stdout.decode().strip()
        # privateToBytes = bytes(private_key,'utf-8')
        # (stdoutData, stderrData) = proc.communicate(privateToBytes)
        # public_key=stdoutData.decode().strip()
        # address = settings.WG_DEFAULT_ADDRESS.replace('x', '1')
        # self.private_key = private_key
        # self.public_key = public_key
        # self.address = address
        # return self


class WGInterfaceUpdate(WGInterface):
    pass


class WGInterfaceInDb(WGInterface):
    id: int
    private_key: str
    public_key: str
    address: str

    class Config:
        from_attributes = True


class WGInterfacePeer(BaseModel):
    """
    *In daemon Interface's Peer configs
    """
    public_key: str
    preshared_key: str
    address: str | None = None
    persistent_keepalive: int | None = None
    last_handshake_at: datetime.datetime | None = None
    rx_bytes: int | None = 0
    tx_bytes: int | None = 0
    protocol_version: int | None = None
    # family: int | None = None
    endpoint_addr: str | None = None
    endpoint_port: int | None = None
    allowed_ips: list[str] | None = None


class WGInterfaceConfig(BaseModel):
    """
    *In daemon WG Interface configs
    """
    listen_port: int
    fwmark: int | None = None
    interface_index: int
    interface_name: str
    private_key: str
    public_key: str
    peers: list[WGInterfacePeer]
