import subprocess
from pydantic import BaseModel, model_validator
from typing import Optional
from app.core.Settings import get_settings

settings = get_settings()


class WGInterface(BaseModel):
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    address: Optional[str] = None
    port: Optional[int] = None
    interface: Optional[str] = None
    mtu: Optional[int] = None


class WGInterfaceCreate(WGInterface):
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    address: Optional[str] = None
    port: Optional[int] = None
    interface: Optional[str] = None

    @model_validator(mode="after")
    def create_server(self):
        private_key = subprocess.run(["wg", "genkey"], capture_output=True).stdout
        public_key = subprocess.run(
            ["wg", "pubkey"],
            input=private_key,
            capture_output=True,
            # executable='/bin/bash'
        ).stdout

        self.address = settings.WG_DEFAULT_ADDRESS.replace("x", "1")
        self.private_key = private_key.decode().strip()
        self.public_key = public_key.decode().strip()
        # address = str(settings.WG_HOST_IP),
        self.port = settings.WG_HOST_PORT
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
