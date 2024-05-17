"""adding client id secret and scope

Revision ID: 5243fc566f2c
Revises: 
Create Date: 2024-05-17 01:48:38.727967+03:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5243fc566f2c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_superuser', sa.Boolean(), nullable=True),
    sa.Column('client_id', sa.String(length=255), nullable=True),
    sa.Column('client_secret', sa.String(length=255), nullable=True),
    sa.Column('scope', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('client_id')
    )
    op.create_index(op.f('ix_user_created_at'), 'user', ['created_at'], unique=False)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=True)
    op.create_index(op.f('ix_user_updated_at'), 'user', ['updated_at'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('wginterface',
    sa.Column('private_key', sa.String(length=255), nullable=False),
    sa.Column('public_key', sa.String(length=255), nullable=True),
    sa.Column('address', sa.String(length=255), nullable=False),
    sa.Column('port', sa.Integer(), nullable=False),
    sa.Column('interface', sa.String(length=50), nullable=False),
    sa.Column('mtu', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
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
    sa.Column('public_key', sa.String(length=256), nullable=False),
    sa.Column('private_key', sa.String(length=256), nullable=False),
    sa.Column('preshared_key', sa.String(length=256), nullable=False),
    sa.Column('latest_handshake_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('persistent_keepalive', sa.Integer(), nullable=True),
    sa.Column('transfer_rx', sa.Integer(), nullable=False),
    sa.Column('transfer_tx', sa.Integer(), nullable=False),
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
    op.create_index(op.f('ix_peer_latest_handshake_at'), 'peer', ['latest_handshake_at'], unique=False)
    op.create_index(op.f('ix_peer_name'), 'peer', ['name'], unique=False)
    op.create_index(op.f('ix_peer_updated_at'), 'peer', ['updated_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_peer_updated_at'), table_name='peer')
    op.drop_index(op.f('ix_peer_name'), table_name='peer')
    op.drop_index(op.f('ix_peer_latest_handshake_at'), table_name='peer')
    op.drop_index(op.f('ix_peer_id'), table_name='peer')
    op.drop_index(op.f('ix_peer_created_at'), table_name='peer')
    op.drop_table('peer')
    op.drop_index(op.f('ix_wginterface_updated_at'), table_name='wginterface')
    op.drop_index(op.f('ix_wginterface_id'), table_name='wginterface')
    op.drop_index(op.f('ix_wginterface_created_at'), table_name='wginterface')
    op.drop_table('wginterface')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_updated_at'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_created_at'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
