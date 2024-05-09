from typing import Optional
from pydantic import BaseModel
from pydantic.types import ByteSize

class WGPeer(BaseModel):
    description:str='description'
    comments:Optional[str]=None
    address:Optional[str]=None
    endpoint:Optional[str]=None
    port:Optional[int]=None
    private_key:Optional[str]=None
    public_key:Optional[str]=None
    preshared_key:Optional[str]=None
    keepalive:Optional[str]=None
    allowed_ips:Optional[str]=None
    save_config:Optional[str]=None
    dns:Optional[str]=None
    pre_up:Optional[str]=None
    post_up:Optional[str]=None
    pre_down:Optional[str]=None
    post_down:Optional[str]=None
    interface:Optional[str]=None
    mtu:Optional[int]=None
    table:Optional[str]=None
    peers:Optional[str]=None
    config_cls:Optional[str]=None
    service_cls:Optional[str]=None
    class Config:
        from_attributes=True