from wireguard import Config,Interface,Server,ServerConfig,Peer
from wireguard.utils import find_ip_and_subnet
from app.core.Settings import get_settings
from app.db.session import get_session,SessionFactory
from app.models.client import Client
from app.schemas.peer import WGPeer
from app.models.wgserver import WGServer
settings = get_settings()

with SessionFactory() as db:
    db_server = db.query(WGServer).first()
    db_peers = db.query(Client).all()
    schema_peers = [ 
        WGPeer(
            address=client.address,
            allowed_ips=client.allowedIPs,
            # endpoint='192.168.1.55',
            private_key=client.privateKey,
            public_key=client.publicKey,
            preshared_key=client.preSharedKey,
            port=settings.WG_PORT,
            interface=settings.WG_DEVICE,
            mtu=settings.WG_MTU,
            # keepalive
            # table
        
        ).model_dump(exclude_none=False) for client in db_peers]
    # print(schema_peers[0])
import subprocess
genpsk = subprocess.run(['wg', 'genpsk'],stderr=subprocess.PIPE,stdout=subprocess.PIPE).stdout.decode().strip()
server = Server(
    description='description',
    subnet=f"{settings.WG_DEFAULT_ADDRESS.replace('x', '0')}/24",
    comments="None",
    # address=None,
    # endpoint=None,
    port=settings.WG_PORT,
    private_key=db_server.privateKey,
    public_key=db_server.publicKey,
    # preshared_key=genpsk,
    # keepalive=None,
    # allowed_ips=None,
    # save_config=None,
    # dns=None,
    pre_up=settings.WG_PRE_UP,
    post_up=settings.WG_POST_UP,
    pre_down=settings.WG_PRE_DOWN,
    post_down=settings.WG_POST_DOWN,
    interface=settings.WG_DEVICE,
    mtu=settings.WG_MTU,
    # table=None,
    peers=schema_peers,
    # config_cls=None,
    # service_cls=None,
)
ce=server.peer(description='peer 1')
a = ce.public_key
server.config.write(config_path=settings.WG_CONFIG_PATH)
print("--> here ",ce)
with SessionFactory() as db:
    db.add(
        Client(
            name="ce",
            address=str(ce.address.pop()),
            publicKey=ce.public_key,
            privateKey=ce.private_key,
            preSharedKey=ce.private_key,
            enabled=True,
            wgserver_id=db_server.id
        )
    )
    db.commit()
    db.close()
# print(server.config)
# print(server.)