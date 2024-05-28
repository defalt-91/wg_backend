import json
import secrets
import subprocess
from functools import lru_cache
from ipaddress import IPv4Address, IPv4Interface, IPv6Interface
from pathlib import Path
from typing import Literal, Optional, Self

from pydantic import Field, IPvAnyAddress, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# import secrets; print(secrets.token_urlsafe(32))
# openssl rand -hex 32


def execute(cmd: list[str], input_value = None, check: bool = False):
    if input:
        return subprocess.run(
            cmd,
            input = input_value,
            text = True,
            encoding = "utf-8",
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
        encoding = "utf-8",
    )


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
    DEBUG: bool = False
    LOG_LEVEL: Literal["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    model_config = SettingsConfigDict(env_file = BASE_DIR / ".env", env_file_encoding = 'utf-8')
    # APP_USER: str | int = 1000
    # APP_GROUP: str | int = 1000
    DIST_DIR: Path | None = None
    # ALEMBIC_CONFIG_PATH: Path | None = BASE_DIR / 'alembic.ini'
    DOMAIN: str = "localhost"
    SECRET_KEY: str = Field(default = secrets.token_urlsafe(32))
    API_ADDRESS: str = "/api/v1"
    ALGORITHM: Optional[str] = "HS256"

    """
    sqlalchemy configs
    """
    # SQLALCHEMY_DATABASE_URI: str = "sqlite:///./sqlite.db"
    # SQLITE_DIR_PATH: Path = Field(default = Path("var/lib/wireguard"))
    SQLITE_FILE_NAME: str | None = None
    SQLALCHEMY_ECHO_QUERIES_TO_STDOUT: bool = False

    """ 
    gunicorn confs
     """
    UVICORN_PORT: int = 8000
    UVICORN_HOST: IPv4Address = "0.0.0.0"
    PROJECT_NAME: str = Field(default = "gunicorn")
    BACKEND_CORS_ORIGINS: list[str]
    BACKEND_ALLOWED_HOSTS: list[str]
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    USERS_OPEN_REGISTRATION: bool = False
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 180
    WORKERS_PER_CORE: int = 2
    MAX_WORKERS: int | None = None
    WEB_CONCURRENCY: int | None = None
    GRACEFUL_TIMEOUT: int = 120
    TIMEOUT: int = 120
    KEEP_ALIVE: int = 5

    """ 
    Wireguard interface configs
    """
    WG_INTERFACE_NAME: str = "wg0"
    WG_SUBNET: IPv4Interface | IPv6Interface = Field(default = '10.200.200.0/24')
    NET_DEVICE: str = Field(default_factory = find_local_network_device(find_interface = True))
    WG_HOST_IP: IPvAnyAddress = Field(default_factory = find_local_network_device(find_interface = False))
    WG_DEFAULT_ADDRESS: str = "10.8.0.x"
    WG_LISTEN_PORT: int = 51820
    WG_MTU: int | None = None
    WG_PERSISTENT_KEEPALIVE: int = 25
    WG_DEFAULT_DNS: IPvAnyAddress = "1.1.1.1"
    WG_PRE_UP: str = ""
    WG_POST_UP: str | None = None
    WG_POST_DOWN: str | None = None
    WG_PRE_DOWN: str = ""
    # LANG: str = "en"

    """ email """
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = 'info@example.com'
    SMTP_TLS: bool | None = None
    SMTP_SSL: bool | None = None
    SMTP_PORT: int | None = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int | None = 24
    EMAILS_FROM_NAME: str | None = None

    """ for future developments """
    TUNNEL_MODE: bool = True

    @model_validator(mode = 'after')
    def verify_configs(self) -> Self:
        if self.DEBUG:
            """   DEBUG mode configurations    """
            if not self.DIST_DIR:
                self.DIST_DIR = BASE_DIR / "dist" / "debug"
            self.PROJECT_NAME = f"{self.PROJECT_NAME}-debug"
        else:
            """   PRODUCTION mode configurations    """
            self.LOG_LEVEL = "WARNING" if not self.LOG_LEVEL else self.LOG_LEVEL
            if not self.DIST_DIR:
                self.DIST_DIR = BASE_DIR / "dist" / "production"
        self.SQLITE_FILE_NAME = f"{self.PROJECT_NAME}.db" if not self.SQLITE_FILE_NAME else self.SQLITE_FILE_NAME
        if (not self.WG_POST_UP) and self.TUNNEL_MODE:
            self.WG_POST_UP = (
                f"iptables -t nat -A POSTROUTING -s {self.WG_SUBNET} -o {self.NET_DEVICE} -j MASQUERADE; "
                f"iptables -A INPUT -p udp -m udp --dport {self.WG_LISTEN_PORT} -j ACCEPT; "
                f"iptables -A FORWARD -i {self.WG_INTERFACE_NAME} -o %i -j ACCEPT; "
                f"iptables -A FORWARD -i %i -o {self.WG_INTERFACE_NAME} -j ACCEPT; "
                f"wg addconf %i {self.wg_if_peers_config_file_path};"
            )
        if (not self.WG_POST_DOWN) and self.TUNNEL_MODE:
            self.WG_POST_DOWN = (
                f"iptables -t nat -D POSTROUTING -s {self.WG_SUBNET} -o {self.NET_DEVICE} -j MASQUERADE; "
                f"iptables -D INPUT -p udp -m udp --dport {self.WG_LISTEN_PORT} -j ACCEPT; "
                f"iptables -A FORWARD -i %i -o {self.WG_INTERFACE_NAME} -j ACCEPT; "
                f"iptables -A FORWARD -i {self.WG_INTERFACE_NAME} -o %i -j ACCEPT; "
                f"#SaveConfig = true"
            )
        return self

    @computed_field()
    @property
    def app_umask_dirs_oct(self) -> int:
        return 0o777

    @computed_field  # type: ignore[misc]
    @property
    def wg_if_peers_config_file_path(self) -> Path:
        return self.wg_config_dir_path / f"{self.WG_INTERFACE_NAME}-peers.conf"

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_bind_value(self) -> str:
        if self.DEBUG:
            return f"{self.UVICORN_HOST}:{self.UVICORN_PORT}"
        return f"unix:{self.run_dir_path / str('gunicorn.' + self.PROJECT_NAME)}.sock"

    @computed_field()
    @property
    def run_dir_path(self) -> Path:
        return self.DIST_DIR / "run"

    @computed_field()
    @property
    def tmp_dir_path(self) -> Path:
        return self.DIST_DIR / "tmp"

    @computed_field()
    @property
    def wg_config_dir_path(self) -> Path:
        return self.DIST_DIR / 'etc/wireguard'

    @computed_field()
    @property
    def pid_file_dir_path(self) -> Path:
        return self.DIST_DIR / "var/run"

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_pid_file(self) -> Path:
        return self.pid_file_dir_path / f"gunicorn.{self.PROJECT_NAME}.pid"

    @computed_field()
    @property
    def sqlite_dir_path(self) -> Path:
        return self.DIST_DIR / "var/lib/wireguard"

    @computed_field()
    @property
    def gunicorn_logs_dir_path(self) -> Path:
        return self.DIST_DIR / "var/log/gunicorn"

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_access_log_path(self) -> Path | str:
        return self.gunicorn_logs_dir_path / f"{self.PROJECT_NAME}.access.log" if not self.DEBUG else '-'

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_error_log_path(self) -> Path | str:
        return self.gunicorn_logs_dir_path / f"{self.PROJECT_NAME}.error.log" if not self.DEBUG else '-'

    @computed_field  # type: ignore[misc]
    @property
    def wg_if_config_file_path(self) -> Path:
        return self.wg_config_dir_path / f"{self.WG_INTERFACE_NAME}.conf"

    @computed_field  # type: ignore[misc]
    @property
    def api_server_address(self) -> str:
        return f"{self.WG_HOST_IP}:{self.WG_LISTEN_PORT}{self.API_ADDRESS}"

    @computed_field  # type: ignore[misc]
    @property
    def sqlalchemy_database_uri(self) -> str:
        return f"sqlite:///{self.sqlite_dir_path}/{self.SQLITE_FILE_NAME}"

    @computed_field()
    @property
    def app_umask_oct(self) -> int:
        """ rwx for owner, wx for group, others none """
        return 0o700

    @computed_field  # type: ignore[misc]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)


@lru_cache
def get_settings() -> BaseConfig:
    return BaseConfig()
