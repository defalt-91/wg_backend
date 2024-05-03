from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import HttpUrl,IPvAnyAddress,field_validator
from dotenv import load_dotenv

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    BACKEND_CORS_ORIGINS:list[str]
    WORKERS_PER_CORE:int=1
    MAX_WORKERS :int= 1
    WEB_CONCURRENCY:int= 1
    BACKEND_SERVER_HOST:str='0.0.0.0'
    BACKEND_SERVER_PORT:int=8008
    LOG_LEVEL:str
    ACCESS_LOG:str="-"
    ERROR_LOG:str
    GRACEFUL_TIMEOUT:int=120
    TIMEOUT:int=120
    KEEP_ALIVE:int=5

    # @field_validator('BACKEND_CORS_ORIGINS',mode='after')
    # @classmethod
    # def turl_url_to_str(cls,v):
    #     str_list:list[str] = []
    #     for i in v:
    #         str_list.append(str(i))
    #         print(str(i))
    #     return ['http://localhost:4200/']
    SESSION_SECRET:str='secret'
    SECRET_KEY:str='secret'
    FIRST_SUPERUSER:str='admin'
    FIRST_SUPERUSER_PASSWORD:str='admin'
    USERS_OPEN_REGISTRATION:bool
    PROJECT_NAME :str = 'any'
    WG_PATH:str
    PORT:int = 51821
    WEBUI_HOST:IPvAnyAddress = '0.0.0.0'
    G_PATH:str = '/etc/wireguard/'
    WG_DEVICE:str = 'enp0s31f6'
    WG_HOST:IPvAnyAddress = '192.168.1.55'
    WG_PORT:int = 51870
    WG_MTU:int = 1420
    WG_PERSISTENT_KEEPALIVE:int = 0
    WG_DEFAULT_ADDRESS:str = '10.8.0.x'
    WG_DEFAULT_DNS:IPvAnyAddress = '1.1.1.1'
    WG_ALLOWED_IPS:str = '0.0.0.0/0, ::/0'
    WG_PRE_UP:str = ''
    WG_PRE_DOWN:str = ''
    WG_POST_UP:str
    LANG:str = 'en'
    UI_TRAFFIC_STATS :bool= True
    SQLALCHEMY_DATABASE_URL:str = "sqlite:///./sqlite.db"
    # SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
    DEBUG:bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
