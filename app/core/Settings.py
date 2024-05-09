from functools import lru_cache
import os
from typing import Optional
from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import HttpUrl,IPvAnyAddress,field_validator,model_validator
from pydantic.networks import AnyHttpUrl
from dotenv import load_dotenv

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    WORKERS_PER_CORE:int=1
    MAX_WORKERS :int= 1
    WEB_CONCURRENCY:int= 1
    BACKEND_CORS_ORIGINS:list[str]
    BACKEND_SERVER_HOST:str='0.0.0.0'
    BACKEND_SERVER_PORT:int=8008
    LOG_LEVEL:str
    ACCESS_LOG:str="-"
    ERROR_LOG:str
    GRACEFUL_TIMEOUT:int=120
    TIMEOUT:int=120
    KEEP_ALIVE:int=5
    SESSION_SECRET:str='secret'
    SECRET_KEY:str='secret'
    FIRST_SUPERUSER:str='admin'
    FIRST_SUPERUSER_PASSWORD:str='admin'
    USERS_OPEN_REGISTRATION:bool
    PROJECT_NAME :Optional[str] = 'any'
    WG_CONFIG_PATH:Optional[str] = "/etc/wireguard/"
    # PORT:int = 51821
    WEBUI_HOST:IPvAnyAddress = '0.0.0.0'
    WG_DEVICE:str
    WG_INTERFACE:Optional[str] = 'wg0'
    WG_HOST:IPvAnyAddress = '192.168.1.55'
    WG_PORT:Optional[int] = 51820
    WG_MTU:Optional[int] = None
    WG_PERSISTENT_KEEPALIVE:Optional[int] = 0
    WG_DEFAULT_ADDRESS:Optional[str] = '10.8.0.x'
    WG_DEFAULT_DNS:Optional[IPvAnyAddress] = '1.1.1.1'
    WG_ALLOWED_IPS:Optional[str] = '0.0.0.0/0, ::/0'
    WG_PRE_UP:Optional[str]=''
    WG_PRE_DOWN:Optional[str]=''
    WG_POST_UP:Optional[str]=''
    WG_POST_DOWN:Optional[str]=''
    LANG:Optional[str] = 'en'
    UI_TRAFFIC_STATS :bool= True
    SQLALCHEMY_DATABASE_URL:str = "sqlite:///./sqlite.db"
    # SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
    DEBUG:bool = True
    WG_SUBNET:Optional[str]=None

    @model_validator(mode="after")
    def create_post_up_str(self):
        self.WG_SUBNET = f"{self.WG_DEFAULT_ADDRESS.replace('x','0')}/24"
        if not self.WG_POST_UP:
            WG_POST_UP_STR = [
                f"iptables -t nat -A POSTROUTING -s {self.WG_DEFAULT_ADDRESS.replace('x', '0')}/24 -o {self.WG_DEVICE} -j MASQUERADE;",
                "iptables -A INPUT -p udp -m udp --dport 51820 -j ACCEPT;",
                "iptables -A FORWARD -i %i -o wg0 -j ACCEPT;",
                "iptables -A FORWARD -i wg0 -o %i -j ACCEPT;",
                f"wg addconf %i {self.WG_CONFIG_PATH}{self.WG_INTERFACE}-peers.conf;"
            ]
            self.WG_POST_UP = ' '.join(WG_POST_UP_STR)
        if not self.WG_POST_DOWN:
            WG_POST_DOWN_STR = [
                f"iptables -t nat -D POSTROUTING -s {self.WG_DEFAULT_ADDRESS.replace('x', '0')}/24 -o {self.WG_DEVICE} -j MASQUERADE;",
                "iptables -D INPUT -p udp -m udp --dport 51820 -j ACCEPT;",
                "iptables -A FORWARD -i %i -o wg0 -j ACCEPT;",
                "iptables -A FORWARD -i wg0 -o %i -j ACCEPT;",
                # "PostUp = wg addconf %i /etc/wireguard/wg0-peers.conf"
            ]
            self.WG_POST_DOWN= ' '.join(WG_POST_DOWN_STR)
        return self
# PostUp = wg addconf %i /etc/wireguard/wg0-peers.conf
@lru_cache
def get_settings() -> Settings:
    return Settings()
