from pydantic import BaseModel,model_validator
from typing import Optional
import subprocess
from app.core.Settings import get_settings
setttings = get_settings()


class WGServerBase(BaseModel):
    privateKey:Optional[str]=None
    publicKey:Optional[str]=None
    address:Optional[str]=None
    
        
class WGServerCreate(WGServerBase):
    privateKey:str
    publicKey:str
    address:str
    # @model_validator(mode='after')
    # def create_server(self):
        # command = ["wg","pubkey"]
        # proc = subprocess.Popen(
        #     command,
        #     stdin=subprocess.PIPE,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        #     # executable='/bin/bash'
        # )
        # privateKey = subprocess.run(['wg', 'genkey'],stdout=subprocess.PIPE).stdout.decode().strip()
        # privateToBytes = bytes(privateKey,'utf-8')
        # (stdoutData, stderrData) = proc.communicate(privateToBytes)
        # publicKey=stdoutData.decode().strip()
        # address = setttings.WG_DEFAULT_ADDRESS.replace('x', '1')
        # self.privateKey = privateKey
        # self.publicKey = publicKey
        # self.address = address
        # return self

class WGServerUpdate(WGServerBase):
    pass
class WGServerInDB(WGServerBase):
    id:int
    privateKey:str
    publicKey:str
    address:str
    class Config:
        from_attributes = True