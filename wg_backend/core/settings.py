import json
import secrets
import subprocess
from functools import lru_cache
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


# BASE_DIR = Path(__file__).parent.parent.parent


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


BASE_DIR: Path = Path(__file__).parent.parent.parent


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file = BASE_DIR / ".env", env_file_encoding = 'utf-8')
    APP_USER: str | int = 1000
    APP_GROUP: str | int = 1000
    APP_UMASK: int = 0o600
    APP_DIRS_UMASK: int = 0o700
    GUNICORN_PORT: int = 8000
    TMP_DIR: Path = Path('/tmp').resolve()
    DIST_DIR: Path = (BASE_DIR / "dist").resolve()
    RUN_DIR: Path = Field(default = Path("var/run"))
    ALEMBIC_CONFIG_PATH: Path | None = BASE_DIR / 'alembic.ini'
    DEBUG: bool = True
    STAGE: bool = True
    LOG_LEVEL: Literal["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | None = None
    DOMAIN: str = "localhost"
    SECRET_KEY: str = Field(default = secrets.token_urlsafe(32))
    API_ADDRESS: str = "/api/v1"
    ALGORITHM: Optional[str] = "HS256"
    UI_TRAFFIC_STATS: bool = True

    """
    sqlalchemy configs
    """
    # SQLALCHEMY_DATABASE_URI: str = "sqlite:///./sqlite.db"
    SQLITE_DIR_PATH: Path = Field(default = Path("var/lib/wireguard"))
    SQLITE_FILE_NAME: str = Field(default = "wireguard.sqlite.db")
    SQLALCHEMY_ECHO_QUERIES_TO_STDOUT: bool = False

    """ 
    gunicorn confs
     """
    GUNICORN_PROC_NAME: str = Field(default = "gunicorn")
    GUNICORN_BIND: str = '0.0.0.0:8080'
    LOGS_DIR_PATH: Path = Field(default = Path("var/log/gunicorn"))
    BACKEND_CORS_ORIGINS: list[str]
    BACKEND_ALLOWED_HOSTS: list[str]
    WORKERS_PER_CORE: int
    MAX_WORKERS: int | None = None
    WEB_CONCURRENCY: int | None = None
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
    WG_CONFIG_DIR_PATH: Path = Field(default = Path('etc/wireguard'))
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
        """   DEBUG mode configurations    """
        if self.DEBUG:
            self.DIST_DIR = self.DIST_DIR / "debug"
            self.SQLITE_DIR_PATH = self.DIST_DIR / self.SQLITE_DIR_PATH
            self.WG_CONFIG_DIR_PATH = self.DIST_DIR / self.WG_CONFIG_DIR_PATH
            self.LOGS_DIR_PATH = self.DIST_DIR / self.LOGS_DIR_PATH
            self.TMP_DIR = self.DIST_DIR / "tmp"
            """
            Gunicorn logs to stdout when its access_log and error_log value is '-'
            """
            self.LOG_LEVEL = "DEBUG" if not self.DEBUG else self.LOG_LEVEL
            self.GUNICORN_PROC_NAME = f"{self.GUNICORN_PROC_NAME}-debug"
        elif self.STAGE:
            """  STAGE mode configurations   """
            self.DIST_DIR = self.DIST_DIR / "stage"
            self.SQLITE_DIR_PATH = self.DIST_DIR / self.SQLITE_DIR_PATH
            self.WG_CONFIG_DIR_PATH = self.DIST_DIR / self.WG_CONFIG_DIR_PATH
            self.LOGS_DIR_PATH = self.DIST_DIR / self.LOGS_DIR_PATH
            self.TMP_DIR = self.DIST_DIR / "tmp"
            self.LOG_LEVEL = "INFO" if not self.LOG_LEVEL else self.LOG_LEVEL
            self.GUNICORN_PROC_NAME = f"{self.GUNICORN_PROC_NAME}-stage"
        else:
            """   PRODUCTION mode configurations    """
            self.DIST_DIR = self.DIST_DIR / "production"
            self.GUNICORN_BIND = f"unix:{self.TMP_DIR}{self.GUNICORN_PROC_NAME}.sock"
            self.RUN_DIR = self.DIST_DIR / self.RUN_DIR
            self.TMP_DIR = self.DIST_DIR / self.TMP_DIR
            self.WG_CONFIG_DIR_PATH = self.DIST_DIR / self.WG_CONFIG_DIR_PATH
            self.SQLITE_DIR_PATH = self.DIST_DIR / self.SQLITE_DIR_PATH
            self.LOGS_DIR_PATH = self.DIST_DIR / self.LOGS_DIR_PATH
            # self.LOGS_DIR_PATH = Path("/etc/wireguard")
            # self.WG_CONFIG_DIR_PATH
        """   DEBUG and STAGE mode shared configurations    """
        if self.DEBUG or self.STAGE:
            self.GUNICORN_BIND = f"0.0.0.0:{self.GUNICORN_PORT}"
            self.RUN_DIR = self.DIST_DIR / self.RUN_DIR
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
    def wg_if_peers_config_file_path(self) -> Path:
        return (self.WG_CONFIG_DIR_PATH / f"{self.WG_INTERFACE_NAME}-peers.conf").resolve()

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_pid_file(self) -> Path:
        if self.DEBUG or self.STAGE:
            return self.DIST_DIR / self.RUN_DIR / f"{self.GUNICORN_PROC_NAME}.pid"
        return Path(f"/var/run/{self.GUNICORN_PROC_NAME}.pid")

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_access_log_path(self) -> Path:
        return (self.LOGS_DIR_PATH / "access.log" if not self.DEBUG else '-').resolve()

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_error_log_path(self) -> Path:
        return (self.LOGS_DIR_PATH / "error.log" if not self.DEBUG else '-').resolve()

    @computed_field  # type: ignore[misc]
    @property
    def wg_if_config_file_path(self) -> Path:
        return (self.WG_CONFIG_DIR_PATH / f"{self.WG_INTERFACE_NAME}.conf").resolve()

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
        return str(f"sqlite:///{self.SQLITE_DIR_PATH}/{self.SQLITE_FILE_NAME}")

    # @computed_field  # type: ignore[misc]
    # @property
    # def wg_subnet(self) -> PostgresDsn:
    #     return f"{self.WG_DEFAULT_ADDRESS.replace('x', '0')}/24"


@lru_cache
def get_settings() -> BaseConfig:
    return BaseConfig()
