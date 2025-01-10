"""create loginattempts table

Revision ID: 4f0b2c7f528c
Revises: 089af88eefd6
Create Date: 2025-01-10 19:41:40.063667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f0b2c7f528c'
down_revision: Union[str, None] = '089af88eefd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('login_attempts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('success', sa.Integer(), nullable=True),
    sa.Column('ip_address', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_login_attempts_id'), 'login_attempts', ['id'], unique=False)
    op.create_index(op.f('ix_login_attempts_user_id'), 'login_attempts', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_login_attempts_user_id'), table_name='login_attempts')
    op.drop_index(op.f('ix_login_attempts_id'), table_name='login_attempts')
    op.drop_table('login_attempts')
    # ### end Alembic commands ###
