"""0004_guest_lifecycle

Supports the guest account lifecycle: `last_ip` records where a guest session
came from (audit/abuse metadata only — guests are identified by their token, not
their address), and `last_active` gets an index because the retention sweeper
filters on it.

Revision ID: 0004_guest_lifecycle
Revises: 0003_question_bank
Create Date: 2026-08-07 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0004_guest_lifecycle'
down_revision: Union[str, None] = '0003_question_bank'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 45 chars covers IPv6 including the IPv4-mapped ::ffff:255.255.255.255 form.
    op.add_column('users', sa.Column('last_ip', sa.String(length=45), nullable=True))
    op.create_index('ix_users_last_active', 'users', ['last_active'])


def downgrade() -> None:
    op.drop_index('ix_users_last_active', table_name='users')
    op.drop_column('users', 'last_ip')
