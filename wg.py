# Imports
from pyroute2 import NDB, WireGuard

IFNAME = 'wg1'

# Create a WireGuard interface
with NDB() as ndb:
    with ndb.interfaces.create(kind='wireguard', ifname=IFNAME) as link:
        link.add_ip('10.0.0.1/24')
        link.set(state='up')

# Create WireGuard object
wg = WireGuard()

# Add a WireGuard configuration + first peer
peer = {'public_key': 'TGFHcm9zc2VCaWNoZV9DJ2VzdExhUGx1c0JlbGxlPDM=',
        'endpoint_addr': '8.8.8.8',
        'endpoint_port': 8888,
        'persistent_keepalive': 15,
        'allowed_ips': ['10.0.0.0/24', '8.8.8.8/32']}
wg.set(IFNAME, private_key='RCdhcHJlc0JpY2hlLEplU2VyYWlzTGFQbHVzQm9ubmU=',
       fwmark=0x1337, listen_port=2525, peer=peer)

# Add second peer with preshared key
peer = {'public_key': 'RCdBcHJlc0JpY2hlLFZpdmVMZXNQcm9iaW90aXF1ZXM=',
        'preshared_key': 'Pz8/V2FudFRvVHJ5TXlBZXJvR3Jvc3NlQmljaGU/Pz8=',
        'endpoint_addr': '8.8.8.8',
        'endpoint_port': 9999,
        'persistent_keepalive': 25,
        'allowed_ips': ['::/0']}
wg.set(IFNAME, peer=peer)

# Delete second peer
peer = {'public_key': 'RCdBcHJlc0JpY2hlLFZpdmVMZXNQcm9iaW90aXF1ZXM=',
        'remove': True}
wg.set(IFNAME, peer=peer)

# Get information of the interface
wg.info(IFNAME)

# Get specific value from the interface
wg.info(IFNAME)[0].get('WGDEVICE_A_PRIVATE_KEY')