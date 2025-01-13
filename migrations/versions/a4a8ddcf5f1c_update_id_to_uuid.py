"""update id to uuid

Revision ID: a4a8ddcf5f1c
Revises: f95fb6d1b7d6
Create Date: 2025-01-13 18:20:13.442643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision: str = 'a4a8ddcf5f1c'
down_revision: Union[str, None] = 'f95fb6d1b7d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Add a temporary UUID column
    op.add_column('users', sa.Column('new_id', postgresql.UUID(as_uuid=True)))
    
    # 2. Generate UUIDs for existing rows
    op.execute("UPDATE users SET new_id = gen_random_uuid()")
    
    # 3. Drop the old primary key constraint
    op.execute('ALTER TABLE users DROP CONSTRAINT users_pkey')
    
    # 4. Drop the old id column
    op.drop_column('users', 'id')
    
    # 5. Rename new_id to id
    op.alter_column('users', 'new_id', new_column_name='id')
    
    # 6. Add primary key constraint to the new id column
    op.execute('ALTER TABLE users ADD PRIMARY KEY (id)')

def downgrade():
    # Convert back to integer if needed
    op.execute('ALTER TABLE users DROP CONSTRAINT users_pkey')
    op.add_column('users', sa.Column('new_id', sa.Integer()))
    op.execute('ALTER TABLE users ADD PRIMARY KEY (new_id)')
    op.drop_column('users', 'id')
    op.alter_column('users', 'new_id', new_column_name='id')