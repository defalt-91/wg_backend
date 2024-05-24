import json
import subprocess

from ipaddress import IPv4Interface, IPv6Interface
from pathlib import Path
from typing import Literal, Optional, Self

from pydantic import Field, IPvAnyAddress, IPvAnyInterface, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# import secrets; print(secrets.token_urlsafe(32))
# openssl rand -hex 32


def execute(cmd: list[str], input_value = None, check: bool = False):
    try:
        if input:
            return subprocess.run(
                cmd,
                input = input_value,
                text = True,
                # user = get_settings(),
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
            )
        if check:
            return subprocess.check_call(
                cmd,
                text = True,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                # executable = '/bin/bash'
            )
        return subprocess.run(
            cmd,
            text = True,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            # stdin = subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise Exception(e.output)


BASE_DIR = Path(__file__).parent.parent.parent


def find_local_network_device(find_interface = True):
    def find_local_ip_or_interface() -> str:
        net_if = None
        local_ip = None
        cmd = ["ip", "-j", "-4", "addr", "show", "up", "to", "default"]
        proc = execute(cmd)
        if proc.stderr:
            raise Exception("Can't call linux ip addr")
        json_conf = json.loads(proc.stdout)
        for device in json_conf:
            if device["group"] == "default" and device["addr_info"][0]["scope"] == "global":
                local_ip = device["addr_info"][0]["local"]
                net_if = device["ifname"]
                break
        if not (net_if or local_ip):
            raise Exception("Can't read interface from ip addr")
        return net_if if find_interface else local_ip

    return find_local_ip_or_interface


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file = BASE_DIR / ".env", env_file_encoding = 'utf-8')
    BASE_DIR: Path | None = BASE_DIR
    ALEMBIC_CONFIG_PATH: Path | None = BASE_DIR / 'alembic.ini'
    DEBUG: bool = True
    STAGE: bool = True
    APP_USER: str = 1000
    APP_GROUP: str = 1000
    DOMAIN: str = "localhost"
    SECRET_KEY: str
    API_ADDRESS: str = "/api/v1"
    ALGORITHM: Optional[str] = "HS256"
    UI_TRAFFIC_STATS: bool = True
    BACKEND_SERVER_HOST: str = "localhost"
    BACKEND_SERVER_PORT: int = 8000

    """
    sqlalchemy configs
    """
    # SQLALCHEMY_DATABASE_URI: str = "sqlite:///./sqlite.db"
    SQLITE_DATABASE_LOCATION: Path | None = None
    SQLALCHEMY_ECHO_CREATED_QUERIES: bool = False

    """ 
    gunicorn confs
     """
    BACKEND_CORS_ORIGINS: list[str]
    BACKEND_ALLOWED_HOSTS: list[str]
    WORKERS_PER_CORE: int
    MAX_WORKERS: int | None = None
    WEB_CONCURRENCY: int | None = None
    LOG_LEVEL: Literal["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    ACCESS_LOG: str | Path | None = None
    ERROR_LOG: str | Path | None = None
    GRACEFUL_TIMEOUT: int = 120
    TIMEOUT: int = 120
    KEEP_ALIVE: int = 5
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    USERS_OPEN_REGISTRATION: bool = False
    PROJECT_NAME: Optional[str] = "wg_backend-"

    """ 
    Wireguard interface configs
    """
    WG_INTERFACE_NAME: str = "wg0"
    APP_FILES_DIR: Path = Field(BASE_DIR / 'wg_config')
    WG_CONFIG_DIR_PATH: Path = Field(default = BASE_DIR / 'wg_config' / 'etc/wireguard')
    WG_SUBNET: IPv4Interface | IPv6Interface | None = None
    NET_DEVICE: str = Field(default_factory = find_local_network_device(find_interface = True))
    WG_HOST_IP: IPvAnyAddress = Field(default_factory = find_local_network_device(find_interface = False))
    WG_DEFAULT_ADDRESS: str = "10.8.0.x"
    WG_HOST_PORT: int = 51820
    WG_MTU: int | None = None
    WG_PERSISTENT_KEEPALIVE: int = 25
    WG_DEFAULT_DNS: IPvAnyAddress = "1.1.1.1"
    WG_PRE_UP: str = ""
    WG_POST_UP: str | None = None
    WG_POST_DOWN: str | None = None
    WG_PRE_DOWN: str = ""
    LANG: str = "en"

    """
    JWT Configs
    """
    ACCESS_TOKEN_EXPIRE_MINUTES: int = None
    # ACCESS_TOKEN_KEY_NAME: str | None = None
    """     
    For better exprience
    environments that need be Change    
    """
    SERVER_ID: Optional[int] = 1

    """ email """
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = 'info@example.com'
    SMTP_TLS: bool | None = None
    SMTP_SSL: bool | None = None
    SMTP_PORT: int | None = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int | None = 24
    EMAILS_FROM_NAME: str | None = 'me'

    @model_validator(mode = 'after')
    def verify_configs(self) -> Self:
        if not self.SQLITE_DATABASE_LOCATION:
            self.SQLITE_DATABASE_LOCATION = self.WG_CONFIG_DIR_PATH / Path("/var/lib/wireguard")

        """ Gunicorn logs to stdout when its access_log and error_log value is '-' """
        if not self.ERROR_LOG:
            if self.DEBUG:
                self.ERROR_LOG = '-'
            else:
                self.ERROR_LOG = self.WG_CONFIG_DIR_PATH / Path("var/log/gunicorn/access.log")
        if not self.ACCESS_LOG:
            if self.DEBUG:
                self.ACCESS_LOG = '-'
            else:
                self.ACCESS_LOG = self.WG_CONFIG_DIR_PATH / Path("var/log/gunicorn/error.log")

        if not self.WG_SUBNET:
            self.WG_SUBNET = IPvAnyInterface(f"{self.WG_HOST_IP}/24")
        if not self.WG_POST_DOWN:
            self.WG_POST_DOWN = (
                f"iptables -t nat -D POSTROUTING -s {self.WG_SUBNET} -o {self.NET_DEVICE} -j MASQUERADE; "
                f"iptables -D INPUT -p udp -m udp --dport {self.WG_HOST_PORT} -j ACCEPT; "
                f"iptables -A FORWARD -i %i -o {self.WG_INTERFACE_NAME} -j ACCEPT; "
                f"iptables -A FORWARD -i {self.WG_INTERFACE_NAME} -o %i -j ACCEPT; "
            )
        if not self.WG_POST_UP:
            self.WG_POST_UP = (
                f"iptables -t nat -A POSTROUTING -s {self.WG_SUBNET} -o {self.NET_DEVICE} -j MASQUERADE; "
                f"iptables -A INPUT -p udp -m udp --dport {self.WG_HOST_PORT} -j ACCEPT; "
                f"iptables -A FORWARD -i %i -o {self.WG_INTERFACE_NAME} -j ACCEPT; "
                f"iptables -A FORWARD -i {self.WG_INTERFACE_NAME} -o %i -j ACCEPT; "
                f"wg addconf %i {self.wg_if_peers_config_file_path};"
            )
        return self

    @computed_field  # type: ignore[misc]
    @property
    def api_server_address(self) -> str:
        return f"{self.WG_HOST_IP}:{self.WG_HOST_PORT}{self.API_ADDRESS}"

    @computed_field  # type: ignore[misc]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    @computed_field  # type: ignore[misc]
    @property
    def sqlalchemy_db_uri(self) -> str:
        return str(f"sqlite:///{self.SQLITE_DATABASE_LOCATION}/sqlite.db")

    # @computed_field  # type: ignore[misc]
    # @property
    # def wg_subnet(self) -> PostgresDsn:
    #     return f"{self.WG_DEFAULT_ADDRESS.replace('x', '0')}/24"




