import logging
from app.core.Settings import get_settings
from app.db.session import SessionFactory
from sqlalchemy.orm import Session
from app.crud import user as user_dal
from app.core.Settings import get_settings
from app.models.client import Client
from app.models.wgserver import WGServer
from app.schemas.user import UserInDB
from app.schemas import UserCreate
import logging
from wireguard_tools.wireguard_netlink import WireguardNetlinkDevice,WireguardConfig,WireguardKey,WireguardPeer
import subprocess
import os
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
settings=get_settings()


def init_db(db: Session) -> None:
    """ creating superuser if there is not one  """
    user = user_dal.authenticate(db, username=settings.FIRST_SUPERUSER,password=settings.FIRST_SUPERUSER_PASSWORD)
    if not user:
        logger.info("No superuser,creating one from provided environments ...")
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        super_user = user_dal.create(db, obj_in=user_in)
        logger.info(f"newly created superuser is: {super_user.username}")
        # WGServer
    # orm_wg_server = crud_wgserver.get_server(session=db)

    from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound
    """ load client config from db or create one"""
    try:
        orm_wg_server=db.query(WGServer).one()
        logger.info("loading existing server from database")
        # server = load_existing_server(db_server=orm_wg_server,db_peers=db_clients)
    except NoResultFound:
        logger.info("No server configuration in database, creating one ...")
        # new_server_conf:WGServerCreate = crud_wgserver.new_server_credentials()
        # orm_wg_server = WGServer(**new_server_conf.model_dump())
    # crud_wgserver.save_wgserver_dot_conf(orm_server=orm_wg_server)
        new_private_key = subprocess.run(['wg', 'genkey'],capture_output=True).stdout
        public_key_process = subprocess.run(
            ["wg","pubkey"],
            input=new_private_key,
            capture_output=True,
            # executable='/bin/bash'
        ).stdout

        orm_wg_server=WGServer(
            privateKey = new_private_key.decode().strip(),
            publicKey = public_key_process.decode().strip(),
            address = str(settings.WG_HOST),
            port = settings.WG_PORT,
            interface = settings.WG_INTERFACE,
            mtu = settings.WG_MTU,
        )
        db.add(orm_wg_server)    
        db.commit()
    except MultipleResultsFound:
        logger.info("there are multiple servers in database, loading last one ...")
        orm_wg_server=db.query(WGServer).all().pop()
        # server = load_existing_server(db_server=orm_wg_server,db_peers=db_clients)
    finally:
    # server.config.write(settings.WG_CONFIG_PATH)    
    # server.service.start()
        wgserver_conf = WireguardConfig(
            private_key=orm_wg_server.privateKey,
            fwmark=None,
            listen_port=orm_wg_server.port,
            # peers=orm_wg_server.clients,
            addresses=[settings.WG_HOST],
            # dns_servers=[settings.WG_DEFAULT_DNS],
            mtu=orm_wg_server.mtu,
            predown=[settings.WG_PRE_DOWN],
            postdown=[settings.WG_POST_DOWN],
            preup=[settings.WG_PRE_UP],
            postup=[settings.WG_POST_UP],
            included_applications=None,
            excluded_applications=None,
        )
        conf_to_write = wgserver_conf.to_wgconfig(wgquick_format=True)
        logger.info(f"Writing database server config file to: {settings.WG_CONFIG_PATH}{settings.WG_INTERFACE}.conf")
        with open(f"{settings.WG_CONFIG_PATH}{settings.WG_INTERFACE}.conf",mode='w',encoding='utf-8') as f:
            f.write(conf_to_write)
        peers:list[Client] = orm_wg_server.clients
        peers_conf_to_write=[]
        for peer in peers:
            print('ksdfh',peer.privateKey)
            print('ksdfh',peer.publicKey)
            print('ksdfh',peer.preSharedKey)
            print('ksdfh',peer.address)
            print('ksdfh',peer.allowedIPs)
            print('ksdfh',orm_wg_server.publicKey)
            wgpeer=WireguardPeer(
                friendly_name=peer.name,
                friendly_json=True,
                public_key = peer.publicKey,
                preshared_key = peer.preSharedKey,
                endpoint_host = settings.WG_HOST,
                endpoint_port = settings.WG_PORT,
                allowed_ips = [f"{peer.address}"]if peer.allowedIPs is not None else []
            )
            peers_conf_to_write.extend(wgpeer.as_wgconfig_snippet())
        logger.info(f"Writing peers config file to: {settings.WG_CONFIG_PATH}{settings.WG_INTERFACE}-peers.conf")
        with open(f"{settings.WG_CONFIG_PATH}{settings.WG_INTERFACE}-peers.conf", mode='w', encoding='utf-8') as peers_fh:
            peers_fh.write(os.linesep.join(peers_conf_to_write))
        logger.info("starting wireguard interface with newly writed config ...")
        try:
            subprocess.run(['wg-quick', 'down','wg0']).stdout
            subprocess.run(['wg-quick', 'up' ,'wg0']).stdout
        except Exception as err:
            if err and err.message and err.message.includes('Cannot find device "wg0"'):
                raise Exception('WireGuard exited with the error: Cannot find device "wg0"\nThis usually means that your host\'s kernel does not support WireGuard!',)
        
    # a= WireguardNetlinkDevice(settings.WG_INTERFACE)
    # b=a.get_config()
    # b.add_peer('asdasd')
    # a.set_config(b)
    # print(a)
    # crud_wgserver.sync_wg_quicks_strip()
    
    
if __name__ == "__main__":
    logger.info("Creating initial data")
    with SessionFactory() as session:
        init_db(session)
    logger.info("Initial data created")