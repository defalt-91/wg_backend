from pydantic import BaseModel, model_validator

from wg_backend.core.settings import execute, get_settings


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

    @model_validator(mode = "after")
    def create_server(self):
        private_key = execute(["wg", "genkey"])
        public_key = execute(
            ["wg", "pubkey"],
            input_value = private_key.stdout,
        )
        if not self.address:
            self.address = settings.WG_DEFAULT_ADDRESS.replace("x", "1")
        self.private_key = private_key.stdout.strip()
        self.public_key = public_key.stdout.strip()
        # address = str(settings.WG_HOST_IP),
        self.port = settings.WG_LISTEN_PORT
        if not self.interface:
            self.interface = settings.WG_INTERFACE_NAME
        if settings.WG_MTU:
            self.mtu = settings.WG_MTU
        return self


class WGInterfaceUpdate(WGInterface):
    pass


class WGInterfaceInDb(WGInterface):
    id: int
    private_key: str
    public_key: str
    address: str

    class Config:
        from_attributes = True
