"""adding user model

Revision ID: 23423d8032d9
Revises: 
Create Date: 2024-05-23 03:47:59.727282+03:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23423d8032d9'
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
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('client_id')
    )
    op.create_index(op.f('ix_user_created_at'), 'user', ['created_at'], unique=False)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=True)
    op.create_index(op.f('ix_user_updated_at'), 'user', ['updated_at'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_updated_at'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_created_at'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###