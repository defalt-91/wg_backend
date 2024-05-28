"""adding peer model

Revision ID: c076e73dc4c1
Revises: 
Create Date: 2024-05-28 02:56:55.913782+03:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c076e73dc4c1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('full_name', sa.String(length=255), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_superuser', sa.Boolean(), nullable=True),
    sa.Column('client_id', sa.String(length=255), nullable=True),
    sa.Column('client_secret', sa.String(length=255), nullable=True),
    sa.Column('scope', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id')
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
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('interface_id', sa.Integer(), nullable=False),
    sa.Column('persistent_keepalive', sa.Integer(), nullable=True),
    sa.Column('allowed_ips', sa.String(length=255), nullable=True),
    sa.Column('preshared_key', sa.String(length=256), nullable=True),
    sa.Column('private_key', sa.String(length=256), nullable=False),
    sa.Column('public_key', sa.String(length=256), nullable=False),
    sa.Column('if_public_key', sa.String(length=256), server_default='', nullable=False),
    sa.Column('address', sa.String(length=256), nullable=False),
    sa.Column('transfer_rx', sa.Integer(), nullable=False),
    sa.Column('transfer_tx', sa.Integer(), nullable=False),
    sa.Column('last_handshake_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('endpoint_addr', sa.String(length=256), nullable=True),
    sa.Column('friendly_name', sa.String(length=255), nullable=True),
    sa.Column('friendly_json', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['interface_id'], ['wginterface.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_peer_created_at'), 'peer', ['created_at'], unique=False)
    op.create_index(op.f('ix_peer_id'), 'peer', ['id'], unique=True)
    op.create_index(op.f('ix_peer_last_handshake_at'), 'peer', ['last_handshake_at'], unique=False)
    op.create_index(op.f('ix_peer_name'), 'peer', ['name'], unique=False)
    op.create_index(op.f('ix_peer_updated_at'), 'peer', ['updated_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_peer_updated_at'), table_name='peer')
    op.drop_index(op.f('ix_peer_name'), table_name='peer')
    op.drop_index(op.f('ix_peer_last_handshake_at'), table_name='peer')
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