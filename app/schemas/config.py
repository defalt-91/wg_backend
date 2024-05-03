from pydantic import BaseModel
from app.schemas.client import ClientInDB
from app.schemas.wgserver import WGServerInDB


class AppConfig(BaseModel):
    server:WGServerInDB
    clients:list[ClientInDB]