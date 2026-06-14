"""add hybrid parser slots to intents

Adds nullable columns shopping_theme, entities, constraints to the intents
table. All nullable so existing rows remain valid (backward-compatible).

Revision ID: 002
Revises: 001
Create Date: 2026-06-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable hybrid-parser slot columns to intents."""
    op.add_column(
        "intents",
        sa.Column("shopping_theme", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "intents",
        sa.Column("entities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "intents",
        sa.Column("constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    """Drop the hybrid-parser slot columns."""
    op.drop_column("intents", "constraints")
    op.drop_column("intents", "entities")
    op.drop_column("intents", "shopping_theme")
