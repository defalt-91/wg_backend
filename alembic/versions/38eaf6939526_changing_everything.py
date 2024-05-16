"""changing everything

Revision ID: 38eaf6939526
Revises: 598fd40c1a6a
Create Date: 2024-05-16 01:34:50.366141+03:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38eaf6939526'
down_revision: Union[str, None] = '598fd40c1a6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('peer', sa.Column('public_key', sa.String(length=256), nullable=False))
    op.add_column('peer', sa.Column('private_key', sa.String(length=256), nullable=False))
    op.add_column('peer', sa.Column('preshared_key', sa.String(length=256), nullable=False))
    op.add_column('peer', sa.Column('latest_handshake_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('peer', sa.Column('persistent_keepalive', sa.Integer(), nullable=True))
    op.add_column('peer', sa.Column('transfer_rx', sa.Integer(), nullable=False))
    op.add_column('peer', sa.Column('transfer_tx', sa.Integer(), nullable=False))
    op.drop_index('ix_peer_latestHandshakeAt', table_name='peer')
    op.create_index(op.f('ix_peer_latest_handshake_at'), 'peer', ['latest_handshake_at'], unique=False)
    op.drop_column('peer', 'privateKey')
    op.drop_column('peer', 'publicKey')
    op.drop_column('peer', 'latestHandshakeAt')
    op.drop_column('peer', 'preSharedKey')
    op.drop_column('peer', 'transferRx')
    op.drop_column('peer', 'transferTx')
    op.drop_column('peer', 'persistentKeepalive')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('peer', sa.Column('persistentKeepalive', sa.INTEGER(), nullable=True))
    op.add_column('peer', sa.Column('transferTx', sa.INTEGER(), nullable=False))
    op.add_column('peer', sa.Column('transferRx', sa.INTEGER(), nullable=False))
    op.add_column('peer', sa.Column('preSharedKey', sa.VARCHAR(length=256), nullable=False))
    op.add_column('peer', sa.Column('latestHandshakeAt', sa.TIMESTAMP(), nullable=True))
    op.add_column('peer', sa.Column('publicKey', sa.VARCHAR(length=256), nullable=False))
    op.add_column('peer', sa.Column('privateKey', sa.VARCHAR(length=256), nullable=False))
    op.drop_index(op.f('ix_peer_latest_handshake_at'), table_name='peer')
    op.create_index('ix_peer_latestHandshakeAt', 'peer', ['latestHandshakeAt'], unique=False)
    op.drop_column('peer', 'transfer_tx')
    op.drop_column('peer', 'transfer_rx')
    op.drop_column('peer', 'persistent_keepalive')
    op.drop_column('peer', 'latest_handshake_at')
    op.drop_column('peer', 'preshared_key')
    op.drop_column('peer', 'private_key')
    op.drop_column('peer', 'public_key')
    # ### end Alembic commands ###