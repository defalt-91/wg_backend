from functools import lru_cache
import subprocess, pathlib, json
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import IPvAnyAddress, model_validator

BASE_DIR = pathlib.Path().resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")
    WORKERS_PER_CORE: int = 1
    MAX_WORKERS: int = 1
    WEB_CONCURRENCY: int = 1
    BACKEND_CORS_ORIGINS: list[str]
    BACKEND_SERVER_HOST: str = "0.0.0.0"
    BACKEND_SERVER_PORT: int = 8008
    LOG_LEVEL: str
    ACCESS_LOG: str = "/var/log/gunicorn/access.log"
    ERROR_LOG: str = "/var/log/gunicorn/error.log"
    GRACEFUL_TIMEOUT: int = 120
    TIMEOUT: int = 120
    KEEP_ALIVE: int = 5
    SECRET_KEY: str = "secret"
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
    UI_TRAFFIC_STATS: bool = True
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./sqlite.db"
    DEBUG: bool = True
    WG_SUBNET: Optional[str] = None

    """     
    For better exprience
    environments that need be Change    
    """
    SERVER_ID: Optional[int] = 1

    @model_validator(mode="after")
    def create_post_up_str(self):
        # self.WG_PEERS_CONFIG_PATH = f"{self.WG_CONFIG_DIR_PATH}/{self.WG_INTERFACE}-peers.conf"
        self.WG_HOST_IP, self.WG_DEVICE = self.find_ip_and_interface()
        self.WG_SUBNET = f"{self.WG_DEFAULT_ADDRESS.replace('x','0')}/24"
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
        with open(f"{self.WG_CONFIG_DIR_PATH}/ip_addr_configs.json", "w") as f:
            f.write(json.dumps(json_conf))
        for device in json_conf:
            if device["group"] == "default" and device["addr_info"][0]["scope"] == "global":
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


# PostUp = wg addconf %i /etc/wireguard/wg0-peers.conf
@lru_cache
def get_settings() -> Settings:
    return Settings()
