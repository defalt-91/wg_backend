import subprocess
from pydantic import BaseModel, model_validator
from typing import Optional
from app.core.Settings import get_settings

settings = get_settings()


class WGServerBase(BaseModel):
    privateKey: Optional[str] = None
    publicKey: Optional[str] = None
    address: Optional[str] = None
    port: Optional[int] = None
    interface: Optional[str] = None
    mtu: Optional[int] = None


class WGServerCreate(WGServerBase):
    privateKey: Optional[str] = None
    publicKey: Optional[str] = None
    address: Optional[str] = None
    port: Optional[int] = None
    interface: Optional[str] = None

    @model_validator(mode="after")
    def create_server(self):
        privateKey = subprocess.run(["wg", "genkey"], capture_output=True).stdout
        publicKey = subprocess.run(
            ["wg", "pubkey"],
            input=privateKey,
            capture_output=True,
            # executable='/bin/bash'
        ).stdout

        self.address = settings.WG_DEFAULT_ADDRESS.replace("x", "1")
        self.privateKey = privateKey.decode().strip()
        self.publicKey = publicKey.decode().strip()
        # address = str(settings.WG_HOST_IP),
        self.port = settings.WG_HOST_PORT
        self.interface = settings.WG_INTERFACE
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
        # privateKey = subprocess.run(['wg', 'genkey'],stdout=subprocess.PIPE).stdout.decode().strip()
        # privateToBytes = bytes(privateKey,'utf-8')
        # (stdoutData, stderrData) = proc.communicate(privateToBytes)
        # publicKey=stdoutData.decode().strip()
        # address = settings.WG_DEFAULT_ADDRESS.replace('x', '1')
        # self.privateKey = privateKey
        # self.publicKey = publicKey
        # self.address = address
        # return self


class WGServerUpdate(WGServerBase):
    pass


class WGServerInDB(WGServerBase):
    id: int
    privateKey: str
    publicKey: str
    address: str

    class Config:
        from_attributes = True
