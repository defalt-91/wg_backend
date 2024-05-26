import json
import secrets
import subprocess
from functools import lru_cache
from ipaddress import IPv4Interface, IPv6Interface
from pathlib import Path
from typing import Literal, Optional, Self

from pydantic import Field, IPvAnyAddress, computed_field, model_validator
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
    DEBUG: bool
    model_config = SettingsConfigDict(env_file = BASE_DIR / ".env", env_file_encoding = 'utf-8')
    # APP_USER: str | int = 1000
    # APP_GROUP: str | int = 1000


    LOG_LEVEL: Literal["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    DIST_DIR: Path = BASE_DIR / "dist"
    TMP_DIR: Path = Path('tmp')
    RUN_DIR: Path = Field(default = Path("run"))
    ALEMBIC_CONFIG_PATH: Path | None = BASE_DIR / 'alembic.ini'
    DOMAIN: str = "localhost"
    SECRET_KEY: str = Field(default = secrets.token_urlsafe(32))
    API_ADDRESS: str = "/api/v1"
    ALGORITHM: Optional[str] = "HS256"

    """
    sqlalchemy configs
    """
    # SQLALCHEMY_DATABASE_URI: str = "sqlite:///./sqlite.db"
    SQLITE_DIR_PATH: Path = Field(default = Path("var/lib/wireguard"))
    SQLITE_FILE_NAME: str | None = None
    SQLALCHEMY_ECHO_QUERIES_TO_STDOUT: bool = False

    """ 
    gunicorn confs
     """
    GUNICORN_PORT: int = 8000
    PROJECT_NAME: str = Field(default = "gunicorn")
    # GUNICORN_BIND: str = '0.0.0.0:8080'
    LOGS_DIR_PATH: Path = Field(default = Path("var/log/gunicorn"))
    PID_FILE_DIR: Path = Field(default = Path("var/run"))
    BACKEND_CORS_ORIGINS: list[str]
    BACKEND_ALLOWED_HOSTS: list[str]
    WORKERS_PER_CORE: int = 2
    MAX_WORKERS: int | None = None
    WEB_CONCURRENCY: int | None = None
    GRACEFUL_TIMEOUT: int = 120
    TIMEOUT: int = 120
    KEEP_ALIVE: int = 5
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    USERS_OPEN_REGISTRATION: bool = False

    """ 
    Wireguard interface configs
    """
    WG_INTERFACE_NAME: str = "wg0"
    WG_CONFIG_DIR_PATH: Path = Field(default = Path('etc/wireguard'))
    WG_SUBNET: IPv4Interface | IPv6Interface = Field(default = '10.200.200.0/24')
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
    # LANG: str = "en"

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
            self.LOG_LEVEL = "DEBUG" if not self.DEBUG else self.LOG_LEVEL
            self.DIST_DIR = self.DIST_DIR / "debug"
            self.PROJECT_NAME = f"{self.PROJECT_NAME}-debug"
        else:
            """   PRODUCTION mode configurations    """
            self.LOG_LEVEL = "WARNING" if not self.DEBUG else self.LOG_LEVEL
            self.DIST_DIR = self.DIST_DIR / "production"
            self.RUN_DIR = self.DIST_DIR / self.RUN_DIR

        self.LOGS_DIR_PATH = self.DIST_DIR / self.LOGS_DIR_PATH
        self.SQLITE_DIR_PATH = self.DIST_DIR / self.SQLITE_DIR_PATH
        self.WG_CONFIG_DIR_PATH = self.DIST_DIR / self.WG_CONFIG_DIR_PATH
        self.RUN_DIR = self.DIST_DIR / self.RUN_DIR
        self.TMP_DIR = self.DIST_DIR / self.TMP_DIR
        self.PID_FILE_DIR = self.DIST_DIR / self.PID_FILE_DIR
        if not self.SQLITE_FILE_NAME:
            self.SQLITE_FILE_NAME = f"{self.PROJECT_NAME}.db"
        if not self.WG_POST_UP:
            # iptables -t nat -I POSTROUTING 1 -s 10.200.200.0/24 -o eth0 -j MASQUERADE
            # iptables -I FORWARD 1 -i wg0 -j ACCEPT;
            # iptables -I FORWARD 1 -o wg0 -j ACCEPT;
            self.WG_POST_UP = (
                f"iptables -t nat -A POSTROUTING -s {self.WG_SUBNET} -o {self.NET_DEVICE} -j MASQUERADE; "
                f"iptables -A INPUT -p udp -m udp --dport {self.WG_HOST_PORT} -j ACCEPT; "
                f"iptables -A FORWARD -i {self.WG_INTERFACE_NAME} -o %i -j ACCEPT; "
                f"iptables -A FORWARD -i %i -o {self.WG_INTERFACE_NAME} -j ACCEPT; "
                f"wg addconf %i {self.wg_if_peers_config_file_path};"
            )
            # iptables -t nat -A POSTROUTING -s ${WG_DEFAULT_ADDRESS.replace('x', '0')}/24 -o ${WG_DEVICE} -j MASQUERADE;
        if not self.WG_POST_DOWN:
            # iptables -t nat -D POSTROUTING -s 10.200.200.0/24 -o eth0 -j MASQUERADE
            # iptables -D FORWARD -i wg0 -j ACCEPT;
            # iptables -D FORWARD -o wg0 -j ACCEPT;
            self.WG_POST_DOWN = (
                f"iptables -t nat -D POSTROUTING -s {self.WG_SUBNET} -o {self.NET_DEVICE} -j MASQUERADE; "
                f"iptables -D INPUT -p udp -m udp --dport {self.WG_HOST_PORT} -j ACCEPT; "
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
        return self.WG_CONFIG_DIR_PATH / f"{self.WG_INTERFACE_NAME}-peers.conf"

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_bind_value(self) -> str:
        if self.DEBUG:
            return f"0.0.0.0:{self.GUNICORN_PORT}"
        return f"unix:{self.RUN_DIR / str('gunicorn.' + self.PROJECT_NAME)}.sock"

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_pid_file(self) -> Path:
        # if self.DEBUG:
        #     return self.DIST_DIR / self.RUN_DIR / f"{self.PROJECT_NAME}.pid"
        return self.DIST_DIR / f"var/run/gunicorn.{self.PROJECT_NAME}.pid"

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_access_log_path(self) -> Path | str:
        return self.LOGS_DIR_PATH / f"{self.PROJECT_NAME}.access.log" if not self.DEBUG else '-'

    @computed_field  # type: ignore[misc]
    @property
    def gunicorn_error_log_path(self) -> Path | str:
        return self.LOGS_DIR_PATH / f"{self.PROJECT_NAME}.error.log" if not self.DEBUG else '-'

    @computed_field  # type: ignore[misc]
    @property
    def wg_if_config_file_path(self) -> Path:
        return self.WG_CONFIG_DIR_PATH / f"{self.WG_INTERFACE_NAME}.conf"

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
        return f"sqlite:///{self.SQLITE_DIR_PATH}/{self.SQLITE_FILE_NAME}"

    """ 
    rwx for owner, wx for group, others none
    """

    @computed_field()
    @property
    def app_umask_oct(self) -> int:
        return 0o700
    # @computed_field  # type: ignore[misc]
    # @property
    # def wg_subnet(self) -> PostgresDsn:
    #     return f"{self.WG_DEFAULT_ADDRESS.replace('x', '0')}/24"


@lru_cache
def get_settings() -> BaseConfig:
    return BaseConfig()


config = BaseConfig()
