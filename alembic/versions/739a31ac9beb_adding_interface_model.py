"""adding interface model

Revision ID: 739a31ac9beb
Revises: 23423d8032d9
Create Date: 2024-05-23 03:48:20.551250+03:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '739a31ac9beb'
down_revision: Union[str, None] = '23423d8032d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
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
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_wginterface_updated_at'), table_name='wginterface')
    op.drop_index(op.f('ix_wginterface_id'), table_name='wginterface')
    op.drop_index(op.f('ix_wginterface_created_at'), table_name='wginterface')
    op.drop_table('wginterface')
    # ### end Alembic commands ###