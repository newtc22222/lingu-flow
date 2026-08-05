"""0002_card_position_image_notes

Adds the Quizlet-style card fields: an explicit in-deck display `position`
(independent of SM-2 review order) plus optional `image_url` and `notes`.

Revision ID: 0002_card_position_image_notes
Revises: 0001_initial_schema
Create Date: 2026-08-06 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0002_card_position_image_notes'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'cards',
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column('cards', sa.Column('image_url', sa.Text(), nullable=True))
    op.add_column('cards', sa.Column('notes', sa.Text(), nullable=True))

    # Seed positions so existing decks get a stable, non-degenerate order
    # instead of every card sharing position 0.
    op.execute(
        """
        UPDATE cards SET position = ordered.rn
        FROM (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY deck_id ORDER BY created_at
            ) - 1 AS rn
            FROM cards
            WHERE deck_id IS NOT NULL
        ) AS ordered
        WHERE cards.id = ordered.id
        """
    )


def downgrade() -> None:
    op.drop_column('cards', 'notes')
    op.drop_column('cards', 'image_url')
    op.drop_column('cards', 'position')
