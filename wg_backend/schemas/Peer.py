import datetime
import uuid
from subprocess import PIPE, Popen
from typing import Self

from pydantic import BaseModel, Field, model_validator

from wg_backend.core.settings import execute, get_settings
from wg_backend.models.wg_interface import WGInterface

settings = get_settings()


# class PeerBase(BaseModel):
#     # mtu: int | None = None
#     persistent_keepalive: int | str | None = None
#     transfer_rx: int | None = 0
#     transfer_tx: int | None = 0
#     last_handshake_at: datetime.datetime | None = None
#     fwmark: int | None = None
#     enabled: bool | None = None
#     endpoint_addr: str | None = None
#     endpoint_port: int | None = None
#     address: str | None = None
#     allowed_ips: str | None = None
#     name: str | None = None
#     downloadable_config: bool | None = None
#     private_key: str | None = None
#     public_key: str | None = None
#     preshared_key: str | None = None
#
#     @model_validator(mode = "after")
#     def check_transferRx(self):
#         if self.transfer_rx is None or not isinstance(self.transfer_rx, int):
#             self.transfer_tx = 0
#         if self.transfer_tx is None or not isinstance(self.transfer_tx, int):
#             self.transfer_tx = 0
#         return self


class PeerUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = True


class PeerCreate(PeerUpdate):
    name: str
    interface_id: int | None = None
    persistent_keepalive: int | str = Field(settings.WG_PERSISTENT_KEEPALIVE, alias = "persistent_keepalive")
    allowed_ips: str = Field(default = "0.0.0.0/0, ::/0")
    # preshared_key: str | None = None
    # private_key: str | None = None


class PeerCreateForInterface(PeerCreate):
    if_public_key: str
    private_key: str
    public_key: str
    preshared_key: str | None = Field(default_factory = lambda: execute(["wg", "genpsk"]).stdout.strip())

    @classmethod
    def create_from_if(cls, db_if: WGInterface, peer_in: PeerCreate) -> Self:
        """ genkey: Generates a new private key and writes it to stdout """
        fresh_private_key = execute(["wg", "genkey"]).stdout.strip()
        """ pubkey: Reads a private key from stdin and writes a public key to stdout """
        pubkey_proc = Popen(
            ["wg", "pubkey"],
            stdin = PIPE,
            stdout = PIPE,
            stderr = PIPE,
            # executable='/bin/bash'
        )
        (public_key_stdoutData, public_key_stderrData) = pubkey_proc.communicate(bytes(fresh_private_key, "utf-8"))
        fresh_public_key = public_key_stdoutData.decode().strip()
        return cls(
            **peer_in.model_dump(exclude_none = True,exclude = {"interface_id"}),
            interface_id = db_if.id,
            if_public_key = db_if.public_key,
            private_key = fresh_private_key,
            public_key = fresh_public_key
        )


class DbDataPeer(BaseModel):
    id: uuid.UUID | None = None
    public_key: str | None = None
    name: str | None = None
    enabled: bool | None = True
    # allowed_ips: list[str] | None = ["0.0.0.0/0, ::0"]
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None

    # interface_id: int
    # friendly_name: str | None = None
    # friendly_json: dict | None = None
    downloadable_config: bool | None = False

    @model_validator(mode = "after")
    def check_downloadable_config(self):
        if self.public_key:
            self.downloadable_config = True
        return self

    class Config:
        from_attributes = True


class StdoutRxTxPlusLhaPeer(BaseModel):
    public_key: str
    last_handshake_at: datetime.datetime | None = None
    transfer_rx: int | None = 0
    transfer_tx: int | None = 0

    @classmethod
    def from_rxtx_lha_stdout(cls, rx_rt_str: str, lha_str: str) -> Self:
        public_key, transfer_rx, transfer_tx = rx_rt_str.split('\t')
        public_key, lht = lha_str.split('\t')
        return cls(public_key = public_key, transfer_rx = transfer_rx, transfer_tx = transfer_tx, last_handshake_at = lht)


class StdoutDumpPeer(StdoutRxTxPlusLhaPeer):
    preshared_key: str | None = None
    endpoint_addr: str | None = None
    allowed_ips: str | None = None
    persistent_keepalive: int | str | None = None

    @classmethod
    def from_dump_stdout(cls, dump_str: str):
        (
            public_key,
            preshared_key,
            endpoint_addr,
            allowed_ips,
            last_handshake_at,
            transfer_rx,
            transfer_tx,
            persistent_keepalive
        ) = dump_str.split('\t')
        return cls(
            public_key = public_key,
            preshared_key = preshared_key,
            endpoint_addr = endpoint_addr,
            allowed_ips = allowed_ips,
            last_handshake_at = last_handshake_at,
            transfer_rx = transfer_rx,
            transfer_tx = transfer_tx,
            persistent_keepalive = persistent_keepalive
        )


class DBPlusStdoutPeer(DbDataPeer, StdoutDumpPeer):
    preshared_key: str | None = None
    endpoint_addr: str | None = None
    allowed_ips: str | None = None


# class StdoutInterface(BaseModel):
#     private_key: str | None = None
#     public_key: str | None = None
#     listening_port: int | None = None
#     fwmark: str | None = None
