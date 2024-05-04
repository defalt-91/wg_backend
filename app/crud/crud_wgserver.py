from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.wgserver import WGServer
from app.schemas.wgserver import WGServerCreate,WGServerUpdate
import subprocess
from app.core.Settings import get_settings
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

WG_PRE_UP = settings.WG_PRE_UP
WG_POST_UP_STR_1 = f"""
iptables -t nat -A POSTROUTING -s {settings.WG_DEFAULT_ADDRESS.replace('x', '0')}/24 -o {settings.WG_DEVICE} -j MASQUERADE;
iptables -A INPUT -p udp -m udp --dport 51820 -j ACCEPT;
iptables -A FORWARD -i wg0 -j ACCEPT;
iptables -A FORWARD -o wg0 -j ACCEPT;
""".split('\n')
WG_POST_UP_STR_2 = ' '.join(WG_POST_UP_STR_1)
WG_POST_UP = os.environ.get('WG_POST_UP',WG_POST_UP_STR_2)

WG_PRE_DOWN = settings.WG_PRE_DOWN
WG_POST_DOWN_STR_1 = f"""
iptables -t nat -D POSTROUTING -s {settings.WG_DEFAULT_ADDRESS.replace('x', '0')}/24 -o {settings.WG_DEVICE} -j MASQUERADE;
iptables -D INPUT -p udp -m udp --dport 51820 -j ACCEPT;
iptables -D FORWARD -i wg0 -j ACCEPT;
iptables -D FORWARD -o wg0 -j ACCEPT;
""".split('\n')
WG_POST_DOWN_STR_2 = ' '.join(WG_POST_DOWN_STR_1)
WG_POST_DOWN = os.environ.get('WG_POST_DOWN',WG_POST_DOWN_STR_2)

class CRUDWGServer(CRUDBase[WGServer,WGServerCreate,WGServerUpdate]):
    def get_server_config(self, session: Session) -> WGServer:
        return session.query(self.model).first()

    def save_wgserver_dot_conf(self,orm_server:WGServer):
        result = f"""
# Note: Do not edit this file directly.
# Your changes will be overwritten!

# Server
[Interface]
PrivateKey = {orm_server.privateKey}
Address = {orm_server.address}/24
ListenPort = {settings.WG_PORT}
PreUp = {WG_PRE_UP}
PostUp = {WG_POST_UP}
PreDown = {WG_PRE_DOWN}
PostDown = {WG_POST_DOWN}"""
        # clients = self.config['clients']
        # all_db_clients=db.query(Client).all()
        for client in orm_server.clients:
            if not client.enabled:
                continue
            pre_shared_key=client.preSharedKey
            if pre_shared_key:
                pre_shared_key_str = f'PresharedKey = {pre_shared_key}'
            else:
                pre_shared_key_str = ''
            result += f"""
            
# Client: {client.name} ({client.id})
[Peer]
PublicKey = {client.publicKey}
{pre_shared_key_str}
AllowedIPs = {client.address}/32"""
        logger.debug('Config saving...')
        with open(f"{settings.WG_PATH}wg0.conf","w") as f :
            f.write(result)
        # with open(f"{WG_PATH}wg0.json", "w") as f:
        #     json_object = json.dumps(self.config,indent=4)
            # f.write(json_object)
        logger.debug('Config saved.')
    def new_server_credentials(self):
        command = ["wg","pubkey"]
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # executable='/bin/bash'
        )
        privateKey = subprocess.run(['wg', 'genkey'],stdout=subprocess.PIPE).stdout.decode().strip()
        privateToBytes = bytes(privateKey,'utf-8')
        (stdoutData, stderrData) = proc.communicate(privateToBytes)
        publicKey=stdoutData.decode().strip()
        address = settings.WG_DEFAULT_ADDRESS.replace('x', '1')
        return WGServerCreate(
            address=address,
            privateKey=privateKey,
            publicKey=publicKey
        )
    def sync_wg_quicks_strip(self):
        logger.debug('Config syncing...')
        (exit_code,output)=subprocess.getstatusoutput('wg syncconf wg0 <(wg-quick strip wg0)')
        logger.debug('Config synced.')

    def save_and_sync_wg_config(self,db:Session):
        # client_list =wgserver.clients
        wgserver = self.get_server_config(db)
        self.save_wgserver_dot_conf(orm_server=wgserver)
        self.sync_wg_quicks_strip()
        
crud_wgserver=CRUDWGServer(WGServer)