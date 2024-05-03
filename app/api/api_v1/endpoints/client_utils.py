import subprocess
import json
from datetime import datetime
import os
from fastapi import HTTPException
from app.schemas.client import ClientFromWG, ClientOut
import uuid
import qrcode
from fastapi.logger import logger
import qrcode.image.svg
from app.core.Settings import get_settings
settings=get_settings()

WG_PATH = settings.WG_PATH
PORT = settings.PORT
WEBUI_HOST = settings.WEBUI_HOST
G_PATH = settings.WG_PATH
WG_DEVICE = settings.WG_DEVICE
WG_HOST = settings.WG_HOST
WG_PORT = settings.WG_PORT
WG_MTU = settings.WG_MTU
WG_PERSISTENT_KEEPALIVE = settings.WG_PERSISTENT_KEEPALIVE
WG_DEFAULT_ADDRESS = settings.WG_DEFAULT_ADDRESS

WG_DEFAULT_DNS = settings.WG_DEFAULT_DNS
WG_ALLOWED_IPS =settings.WG_ALLOWED_IPS

WG_PRE_UP = settings.WG_PRE_UP
WG_POST_UP_STR_1 = f"""
iptables -t nat -A POSTROUTING -s {WG_DEFAULT_ADDRESS.replace('x', '0')}/24 -o {WG_DEVICE} -j MASQUERADE;
iptables -A INPUT -p udp -m udp --dport 51820 -j ACCEPT;
iptables -A FORWARD -i wg0 -j ACCEPT;
iptables -A FORWARD -o wg0 -j ACCEPT;
""".split('\n')
WG_POST_UP_STR_2 = ' '.join(WG_POST_UP_STR_1)
WG_POST_UP = os.environ.get('WG_POST_UP',WG_POST_UP_STR_2)

WG_PRE_DOWN = settings.WG_PRE_DOWN
WG_POST_DOWN_STR_1 = f"""
iptables -t nat -D POSTROUTING -s {WG_DEFAULT_ADDRESS.replace('x', '0')}/24 -o {WG_DEVICE} -j MASQUERADE;
iptables -D INPUT -p udp -m udp --dport 51820 -j ACCEPT;
iptables -D FORWARD -i wg0 -j ACCEPT;
iptables -D FORWARD -o wg0 -j ACCEPT;
""".split('\n')
WG_POST_DOWN_STR_2 = ' '.join(WG_POST_DOWN_STR_1)
WG_POST_DOWN = os.environ.get('WG_POST_DOWN',WG_POST_DOWN_STR_2)



class ClientService:
    def __init__(self) -> None:
        self.config = None
        self.logger = logger
    def getConfig(self):        
        if self.config:
            return self.config
        try:
            with open(F"{WG_PATH}wg0.json","r") as f:
                self.config = json.load(f)
        except:
            try:
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
                address = WG_DEFAULT_ADDRESS.replace('x', '1')
                self.config = {
                    "server": {
                        "privateKey":privateKey,
                        "publicKey":publicKey,
                        "address":address,
                    },
                    "clients": {},
                }
                self.logger.debug('New Configuration generated.')
            except Exception:
                raise Exception('here')
        try:
            self.__saveConfig()
        except:
            raise Exception('--> cant save configuration, please run server with sudo previllages')
        try:
            subprocess.run(['wg-quick', 'down','wg0']).stdout
            subprocess.run(['wg-quick', 'up' ,'wg0']).stdout
        except Exception as e:
            raise ExceptionGroup('WireGuard exited with the error: Cannot find device "wg0"\nThis usually means that your host\'s kernel does not support WireGuard!',e)
        # self.__syncConfig()
        return self.config
    

    def get_clients(self):
        config = self.getConfig()
        clients_list = []
        clients = config['clients']
        for client in config['clients']:
            a = ClientOut(
            id=client,
            name=clients[client]['name'],
            enabled=bool(clients[client]['enabled']),
            address=clients[client]['address'],
            publicKey=clients[client]['publicKey'],
            created_at= datetime.fromisoformat(clients[client]['createdAt']),
            updated_at= datetime.fromisoformat(clients[client]['updatedAt']),
            # allowedIPs=[f"{clients[client]['address']}/32"],
            downloadableConfig= 'privateKey' in clients[client],
            persistentKeepalive=None,
            latestHandshakeAt=None,
            transferRx=None,
            transferTx=None,
            )
            clients_list.append(a)
        return clients_list


    def add_config_to_clients(self,clients:list[ClientOut]) -> list[ClientOut]:
        dump = subprocess.run(["wg", "show" ,"wg0", "dump"],stdout=subprocess.PIPE).stdout.decode().strip().splitlines()
        if len(dump):
            del dump[0]
        # dump.pop(0)

        for line in dump :
            (
                publicKey,
                pre_shared_key,
                endpoint,
                allowedIps,
                latestHandshakeAt,
                transferRx,
                transferTx,
                persistentKeepalive
             ) = line.split('\t')
            for client in clients:
                if client.publicKey == publicKey:
                    if latestHandshakeAt != '0':
                        client.latestHandshakeAt = datetime.fromtimestamp(int(latestHandshakeAt))
                    else:
                        client.latestHandshakeAt = None
                    client.persistentKeepalive = persistentKeepalive
                    client.transferRx = int(transferRx or 0)    
                    client.transferTx = int(transferTx or 0)
                    client.allowedIPs.append(allowedIps)
        return clients

    def saveConfig(self) :
        self.__saveConfig()
        self.__syncConfig()


    def __saveConfig(self):
        result = f"""
# Note: Do not edit this file directly.
# Your changes will be overwritten!

# Server
[Interface]
PrivateKey = {self.config['server']['privateKey']}
Address = {self.config['server']['address']}/24
ListenPort = {WG_PORT}
PreUp = {WG_PRE_UP}
PostUp = {WG_POST_UP}
PreDown = {WG_PRE_DOWN}
PostDown = {WG_POST_DOWN}"""
        clients = self.config['clients']
        for clientId in clients :
            if not bool(clients[clientId]['enabled']):
                continue
            pre_shared_key=clients[clientId]['preSharedKey']
            if pre_shared_key:
                pre_shared_key_str = f'PresharedKey = {pre_shared_key}'
            else:
                pre_shared_key_str = ''
            result += f"""
# Client: {clients[clientId]['name']} ({clientId})
[Peer]
PublicKey = {clients[clientId]['publicKey']}
{pre_shared_key_str}
AllowedIPs = {clients[clientId]['address']}/32"""
        self.logger.debug('Config saving...')
        with open(f"{WG_PATH}wg0.conf","w") as f :
            f.write(result)
        with open(f"{WG_PATH}wg0.json", "w") as f:
            json_object = json.dumps(self.config,indent=4)
            f.write(json_object)
        self.logger.debug('Config saved.')

    # def __syncConfig(self) :
    #     self.logger.debug('Config syncing...')
    #     id,res=subprocess.getstatusoutput('wg syncconf wg0 <(wg-quick strip wg0)')
    #     self.logger.debug('Config synced.')

    def getClient( self,clientId ) -> dict :
        config = self.getConfig()
        client = config['clients'][clientId]
        if not client :
            raise HTTPException(f'Client Not Found: {clientId}', 404)
        return client

    def getClientConfiguration(self, clientId ) :
        config = self.getConfig()
        client = self.getClient(clientId)
        priv_key = 'REPLACE_ME'
        if client['privateKey']:
            priv_key=client['privateKey']
        defautl_dns = ''
        if WG_DEFAULT_DNS:
            defautl_dns = f"DNS = {WG_DEFAULT_DNS}\n"
        wg_mtu_str = ''
        if WG_MTU:
            wg_mtu_str = f"MTU = {WG_MTU}\n"
        pre_shared_key_str=''
        if client['preSharedKey']:
            pre_shared_key_str=f"PresharedKey = {client['preSharedKey']}"
        return f"""
[Interface]
PrivateKey = {priv_key}
Address = {client['address']}/24
{defautl_dns}\
{wg_mtu_str}\

[Peer]
PublicKey = {config['server']['publicKey']}
{pre_shared_key_str}
AllowedIPs = {WG_ALLOWED_IPS}
PersistentKeepalive = {WG_PERSISTENT_KEEPALIVE}
Endpoint = {WG_HOST}:{WG_PORT}"""

    def getClientQRCodeSVG(self,clientId) :
        config = self.getClientConfiguration(clientId)
        print('-->config',config)
        method = "fragment"
        if method == 'basic':
            # Simple factory, just a set of rects.
            factory = qrcode.image.svg.SvgImage
        elif method == 'fragment':
            # Fragment factory (also just a set of rects)
            factory = qrcode.image.svg.SvgFragmentImage
        elif method == 'path':
            # Combined path factory, fixes white space that may occur when zooming
            factory = qrcode.image.svg.SvgPathImage
        sqvqrcode = qrcode.make(config,
                                image_factory=factory,
                                box_size=22
                                )
        # qrcode.save('file.svg')
        return sqvqrcode
    
    def look_for_client_address_in_dict(self,address,clients):
        has_or_not = False
        for key in clients:
            if clients[key]['address'] == address:
                has_or_not = True
        return has_or_not
    
    
    def createClient(self,name) :
        config = self.getConfig()
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
        pre_shared_key = subprocess.run(["wg" ,"genpsk"],
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            # executable='/bin/bash'
                                    ).stdout.decode().strip()
        #Calculate next IP
        address=None
        clients:dict = config['clients']
        if len(clients) == 0:
            address = WG_DEFAULT_ADDRESS.replace('x', str(2))
        else:
            for i in range(2,255):
                ip_available = False
                for key in clients:
                    if clients[key]['address'] == WG_DEFAULT_ADDRESS.replace('x', str(i)):
                        ip_available = True
                if not ip_available:
                    address = WG_DEFAULT_ADDRESS.replace('x', str(i))
                    break

        if not address:
            raise Exception('Maximum number of clients reached.')

        # // Create Client
        id = str(uuid.uuid4())
        client = {
            'id':id,
            'name':name, 
            'enabled': 'True',
            'address':address,
            'publicKey':str(publicKey),
            'createdAt': datetime.now().isoformat(),
            'privateKey':str(privateKey),
            'preSharedKey':pre_shared_key,
            'updatedAt': datetime.now().isoformat(),
        }
        config['clients'][id] = client
        self.logger.debug('newly created user',config['clients'][id])
        self.saveConfig()

        return client
  
    def deleteClient(self, clientId:str ) :
        config = self.getConfig()
        if config['clients'][clientId] :
            del config['clients'][clientId] 
            self.saveConfig()

    def update_client(self,client:ClientFromWG) :
        old_client = self.getClient(client.id)
        old_client['enabled'] = bool(client.enabled)
        old_client['name'] = client.name
        old_client['updatedAt'] = datetime.now().isoformat()
        update_config = self.getConfig()
        update_config['clients'][client.id] = old_client
        self.saveConfig()

    def isValidIPv4(self,ip) :
        blocks = ip.split('.')
        if blocks.length != 4 :
            return False

        for value in blocks:
            try:
                value = int(value, 10)
            except:
                return False          
            if value < 0 or value > 255:
                return False
        return True

    def updateClientAddress(self, clientId, address) :
        client = self.getClient(clientId)
        config = self.getConfig()
        if not self.isValidIPv4(address) :
            raise Exception('Invalid Address: {address}', 400)
        client.address = address
        client.updatedAt = datetime.now().isoformat()
        config['clients'][client.id] = client
        self.saveConfig(config)

    def Shutdown() :
        os.system('wg-quick down wg0')
