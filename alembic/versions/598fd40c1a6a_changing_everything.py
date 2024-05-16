"""changing everything

Revision ID: 598fd40c1a6a
Revises: e16249e7b301
Create Date: 2024-05-15 21:04:09.627937+03:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '598fd40c1a6a'
down_revision: Union[str, None] = 'e16249e7b301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('wginterface',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('private_key', sa.String(length=255), nullable=False),
    sa.Column('public_key', sa.String(length=255), nullable=True),
    sa.Column('address', sa.String(length=255), nullable=False),
    sa.Column('port', sa.Integer(), nullable=False),
    sa.Column('interface', sa.String(length=50), nullable=False),
    sa.Column('mtu', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wginterface_created_at'), 'wginterface', ['created_at'], unique=False)
    op.create_index(op.f('ix_wginterface_id'), 'wginterface', ['id'], unique=True)
    op.create_index(op.f('ix_wginterface_updated_at'), 'wginterface', ['updated_at'], unique=False)
    op.create_table('peer',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('address', sa.String(length=256), nullable=False),
    sa.Column('publicKey', sa.String(length=256), nullable=False),
    sa.Column('privateKey', sa.String(length=256), nullable=False),
    sa.Column('preSharedKey', sa.String(length=256), nullable=False),
    sa.Column('latestHandshakeAt', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('persistentKeepalive', sa.Integer(), nullable=True),
    sa.Column('transferRx', sa.Integer(), nullable=False),
    sa.Column('transferTx', sa.Integer(), nullable=False),
    sa.Column('friendly_name', sa.String(length=255), nullable=True),
    sa.Column('friendly_json', sa.String(length=255), nullable=True),
    sa.Column('interface_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['interface_id'], ['wginterface.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_peer_created_at'), 'peer', ['created_at'], unique=False)
    op.create_index(op.f('ix_peer_id'), 'peer', ['id'], unique=True)
    op.create_index(op.f('ix_peer_latestHandshakeAt'), 'peer', ['latestHandshakeAt'], unique=False)
    op.create_index(op.f('ix_peer_name'), 'peer', ['name'], unique=False)
    op.create_index(op.f('ix_peer_updated_at'), 'peer', ['updated_at'], unique=False)
    op.drop_index('ix_client_created_at', table_name='client')
    op.drop_index('ix_client_id', table_name='client')
    op.drop_index('ix_client_latestHandshakeAt', table_name='client')
    op.drop_index('ix_client_name', table_name='client')
    op.drop_index('ix_client_updated_at', table_name='client')
    op.drop_table('client')
    op.drop_index('ix_wgserver_created_at', table_name='wgserver')
    op.drop_index('ix_wgserver_id', table_name='wgserver')
    op.drop_index('ix_wgserver_updated_at', table_name='wgserver')
    op.drop_table('wgserver')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('wgserver',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('privateKey', sa.VARCHAR(length=255), nullable=False),
    sa.Column('publicKey', sa.VARCHAR(length=255), nullable=True),
    sa.Column('address', sa.VARCHAR(length=255), nullable=False),
    sa.Column('port', sa.INTEGER(), nullable=False),
    sa.Column('interface', sa.VARCHAR(length=50), nullable=False),
    sa.Column('mtu', sa.INTEGER(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_wgserver_updated_at', 'wgserver', ['updated_at'], unique=False)
    op.create_index('ix_wgserver_id', 'wgserver', ['id'], unique=1)
    op.create_index('ix_wgserver_created_at', 'wgserver', ['created_at'], unique=False)
    op.create_table('client',
    sa.Column('id', sa.CHAR(length=32), nullable=False),
    sa.Column('name', sa.VARCHAR(length=256), nullable=True),
    sa.Column('enabled', sa.BOOLEAN(), nullable=False),
    sa.Column('address', sa.VARCHAR(length=256), nullable=False),
    sa.Column('publicKey', sa.VARCHAR(length=256), nullable=False),
    sa.Column('privateKey', sa.VARCHAR(length=256), nullable=False),
    sa.Column('preSharedKey', sa.VARCHAR(length=256), nullable=False),
    sa.Column('latestHandshakeAt', sa.TIMESTAMP(), nullable=True),
    sa.Column('persistentKeepalive', sa.INTEGER(), nullable=True),
    sa.Column('transferRx', sa.INTEGER(), nullable=False),
    sa.Column('transferTx', sa.INTEGER(), nullable=False),
    sa.Column('friendly_name', sa.VARCHAR(length=255), nullable=True),
    sa.Column('friendly_json', sa.VARCHAR(length=255), nullable=True),
    sa.Column('wgserver_id', sa.INTEGER(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['wgserver_id'], ['wgserver.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_client_updated_at', 'client', ['updated_at'], unique=False)
    op.create_index('ix_client_name', 'client', ['name'], unique=False)
    op.create_index('ix_client_latestHandshakeAt', 'client', ['latestHandshakeAt'], unique=False)
    op.create_index('ix_client_id', 'client', ['id'], unique=1)
    op.create_index('ix_client_created_at', 'client', ['created_at'], unique=False)
    op.drop_index(op.f('ix_peer_updated_at'), table_name='peer')
    op.drop_index(op.f('ix_peer_name'), table_name='peer')
    op.drop_index(op.f('ix_peer_latestHandshakeAt'), table_name='peer')
    op.drop_index(op.f('ix_peer_id'), table_name='peer')
    op.drop_index(op.f('ix_peer_created_at'), table_name='peer')
    op.drop_table('peer')
    op.drop_index(op.f('ix_wginterface_updated_at'), table_name='wginterface')
    op.drop_index(op.f('ix_wginterface_id'), table_name='wginterface')
    op.drop_index(op.f('ix_wginterface_created_at'), table_name='wginterface')
    op.drop_table('wginterface')
    # ### end Alembic commands ###