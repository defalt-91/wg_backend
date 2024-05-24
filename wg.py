from typing import Tuple, Type

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource
)


class Settings(BaseSettings):
    """Example loading values from the table used by default."""
    # debug: bool
    model_config = SettingsConfigDict(
        # env_file = "test.env",
        toml_file = "prod.env.toml",
        extra = 'ignore'
#         env_file_encoding = 'utf-8'
    )

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: TomlConfigSettingsSource(toml_file="prod.env.toml",settings_cls = BaseSettings),
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        print('-DEBUG value ls:', cls.parse_file)
        return (
        TomlConfigSettingsSource(settings_cls), init_settings, env_settings, dotenv_settings, file_secret_settings)


class SqlalchemySettings(BaseModel):
    dburi: str


class NameTable(BaseModel):
    name: str
    lname: str


class Poetry(BaseModel):
    debug: bool


class ToolTable(BaseModel):
    # wg: NameTable
    poetry: Poetry | None


class ProdConfig(Settings):
    FOOBAR: str
    # sqlalchemy: SqlalchemySettings
    tool: ToolTable
    model_config = SettingsConfigDict(
        toml_file = 'prod.env.toml',
        extra = 'ignore',
        env_file = 'test.env',
        secrets_dir = '/var/secrets',
        # pyproject_toml_table_header=('tool', 'some-table')
    )


class RootSettings(BaseSettings):
    """Example loading values from the root of a testyproject.toml file."""
    tool: ToolTable
    model_config = SettingsConfigDict(
        extra = 'ignore',
        toml_file = 'testyproject.toml',
        # table
        # pyproject_toml_table_header=()
    )


# settings = RootSettings()
# settings2 = DebugConfig()
settings3 = ProdConfig()
# print('-->', settings)
# print('-->', settings2)
print('-->', settings3.model_dump())
# print('-->', settings.model_dump())


# # Imports
# from pyroute2 import NDB, WireGuard
#
# IFNAME = 'wg1'
#
# # Create a WireGuard interface
# with NDB() as ndb:
#     with ndb.interfaces.create(kind='wireguard', ifname=IFNAME) as link:
#         link.add_ip('10.0.0.1/24')
#         link.set(state='up')
#
# # Create WireGuard object
# wg = WireGuard()
#
# # Add a WireGuard configuration + first peer
# peer = {'public_key': 'TGFHcm9zc2VCaWNoZV9DJ2VzdExhUGx1c0JlbGxlPDM=',
#         'endpoint_addr': '8.8.8.8',
#         'endpoint_port': 8888,
#         'persistent_keepalive': 15,
#         'allowed_ips': ['10.0.0.0/24', '8.8.8.8/32']}
# wg.set(IFNAME, private_key='RCdhcHJlc0JpY2hlLEplU2VyYWlzTGFQbHVzQm9ubmU=',
#        fwmark=0x1337, listen_port=2525, peer=peer)
#
# # Add second peer with preshared key
# peer = {'public_key': 'RCdBcHJlc0JpY2hlLFZpdmVMZXNQcm9iaW90aXF1ZXM=',
#         'preshared_key': 'Pz8/V2FudFRvVHJ5TXlBZXJvR3Jvc3NlQmljaGU/Pz8=',
#         'endpoint_addr': '8.8.8.8',
#         'endpoint_port': 9999,
#         'persistent_keepalive': 25,
#         'allowed_ips': ['::/0']}
# wg.set(IFNAME, peer=peer)
#
# # Delete second peer
# peer = {'public_key': 'RCdBcHJlc0JpY2hlLFZpdmVMZXNQcm9iaW90aXF1ZXM=',
#         'remove': True}
# wg.set(IFNAME, peer=peer)
#
# # Get information of the interface
# wg.info(IFNAME)
#
# # Get specific value from the interface
# wg.info(IFNAME)[0].get('WGDEVICE_A_PRIVATE_KEY')
