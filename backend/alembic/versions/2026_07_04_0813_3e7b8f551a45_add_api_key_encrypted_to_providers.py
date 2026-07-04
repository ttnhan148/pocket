"""add_api_key_encrypted_to_providers

Revision ID: 3e7b8f551a45
Revises: e356f1a85cb2
Create Date: 2026-07-04 08:13:26.905290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e7b8f551a45'
down_revision: Union[str, Sequence[str], None] = 'e356f1a85cb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('providers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('api_key_encrypted', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('providers', schema=None) as batch_op:
        batch_op.drop_column('api_key_encrypted')
