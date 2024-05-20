import json
import pathlib
import subprocess
from functools import lru_cache
from typing import Optional

from pydantic import IPvAnyAddress, model_validator, computed_field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = pathlib.Path().resolve()

""" for creating SECRET_KEY locally """


# import secrets; print(secrets.token_urlsafe(32))
# openssl rand -hex 32

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")
    DEBUG: bool = True
    DOMAIN: str
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    API_ADDRESS: str | None = "/api/v1"
    ALGORITHM: Optional[str] = "HS256"
    UI_TRAFFIC_STATS: bool = True
    SQLALCHEMY_DATABASE_URI: str
    BACKEND_SERVER_HOST: str | None = "localhost"
    BACKEND_SERVER_PORT: int | None = 8000
    """ gunicorn confs """
    BACKEND_CORS_ORIGINS: list[str]
    BACKEND_ALLOWED_HOSTS: list[str]
    WORKERS_PER_CORE: int = 1
    MAX_WORKERS: int = 1
    WEB_CONCURRENCY: int = 1
    LOG_LEVEL: str
    ACCESS_LOG: str = "/var/log/gunicorn/access.log"
    ERROR_LOG: str = "/var/log/gunicorn/error.log"
    GRACEFUL_TIMEOUT: int = 120
    TIMEOUT: int = 120
    KEEP_ALIVE: int = 5
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    USERS_OPEN_REGISTRATION: bool
    PROJECT_NAME: Optional[str] = "app-"
    WG_CONFIG_DIR_PATH: str
    WG_DEVICE: Optional[str] = "eth0"
    WG_INTERFACE: Optional[str] = "wg0"
    WG_HOST_IP: IPvAnyAddress = None
    WG_HOST_PORT: Optional[int] = 51820
    WG_MTU: Optional[int] = None
    WG_PERSISTENT_KEEPALIVE: Optional[int] = 0
    WG_DEFAULT_ADDRESS: Optional[str] = "10.8.0.x"
    WG_DEFAULT_DNS: Optional[IPvAnyAddress] = "1.1.1.1"
    WG_PRE_UP: Optional[str] = ""
    WG_PRE_DOWN: Optional[str] = ""
    WG_POST_UP: Optional[str] = ""
    WG_POST_DOWN: Optional[str] = ""
    LANG: Optional[str] = "en"

    """
    JWT Configs
    """
    ACCESS_TOKEN_EXPIRE_MINUTES: int | None = None
    ACCESS_TOKEN_KEY_NAME: str | None = None
    """     
    For better exprience
    environments that need be Change    
    """
    SERVER_ID: Optional[int] = 1

    """ email """
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    SMTP_TLS: bool | None = None
    SMTP_SSL: bool | None = None
    SMTP_PORT: int | None = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int | None = 24
    EMAILS_FROM_NAME: str | None = 'test'

    @computed_field  # type: ignore[misc]
    @property
    def WG_SUBNET(self) -> PostgresDsn:
        return f"{self.WG_DEFAULT_ADDRESS.replace('x', '0')}/24"

    @computed_field  # type: ignore[misc]
    @property
    def api_server_address(self) -> PostgresDsn:
        return f"{self.WG_HOST_IP}:{self.WG_HOST_PORT}{self.API_ADDRESS}"

    @computed_field  # type: ignore[misc]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    @model_validator(mode="after")
    def create_post_up_str(self):
        if not self.ACCESS_TOKEN_KEY_NAME:
            self.ACCESS_TOKEN_KEY_NAME = "access_token"
        # self.WG_PEERS_CONFIG_PATH = f"{self.WG_CONFIG_DIR_PATH}/{self.WG_INTERFACE}-peers.conf"
        self.WG_HOST_IP, self.WG_DEVICE = self.find_ip_and_interface()
        if not self.WG_POST_UP:
            WG_POST_UP_STR = [
                f"iptables -t nat -A POSTROUTING -s {self.WG_DEFAULT_ADDRESS.replace('x', '0')}/24 -o {self.WG_DEVICE} -j MASQUERADE;",
                f"iptables -A INPUT -p udp -m udp --dport {self.WG_HOST_PORT} -j ACCEPT;",
                "iptables -A FORWARD -i %i -o wg0 -j ACCEPT;",
                "iptables -A FORWARD -i wg0 -o %i -j ACCEPT;",
                # f"wg addconf %i {self.peers_file_path};"
            ]
            self.WG_POST_UP = " ".join(WG_POST_UP_STR)
        if not self.WG_POST_DOWN:
            WG_POST_DOWN_STR = [
                f"iptables -t nat -D POSTROUTING -s {self.WG_DEFAULT_ADDRESS.replace('x', '0')}/24 -o {self.WG_DEVICE} -j MASQUERADE;",
                f"iptables -D INPUT -p udp -m udp --dport {self.WG_HOST_PORT} -j ACCEPT;",
                "iptables -A FORWARD -i %i -o wg0 -j ACCEPT;",
                "iptables -A FORWARD -i wg0 -o %i -j ACCEPT;",
                #
            ]
            self.WG_POST_DOWN = " ".join(WG_POST_DOWN_STR)
        return self

    def find_ip_and_interface(self) -> tuple[str, str]:
        cmd = ["ip", "-j", "-4", "addr", "show", "up", "to", "default"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.stderr:
            raise Exception("Can't call linux ip addr")
        json_conf = json.loads(proc.stdout)
        for device in json_conf:
            if device["group"]=="default" and device["addr_info"][0]["scope"]=="global":
                local_ip = device["addr_info"][0]["local"]
                interface = device["ifname"]
                break
        if not local_ip and interface:
            raise Exception("Can't read ip and interface from ip addr")
        return local_ip, interface

    @property
    def wgserver_file_path(self):
        return f"{self.WG_CONFIG_DIR_PATH}/{self.WG_INTERFACE}.conf"

    @property
    def peers_file_path(self):
        return f"{self.WG_CONFIG_DIR_PATH}/{self.WG_INTERFACE}-peers.conf"


@lru_cache
def get_settings() -> Settings:
    return Settings()
