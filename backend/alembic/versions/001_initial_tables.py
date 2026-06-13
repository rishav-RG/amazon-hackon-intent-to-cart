"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-06-13 18:59:24.481367

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all eight tables for the Intent-to-Cart system."""

    # 1. intents table
    op.create_table(
        "intents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("intent_type", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. clarifications table
    op.create_table(
        "clarifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("intent_id", sa.UUID(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["intent_id"],
            ["intents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. bundles table
    op.create_table(
        "bundles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("intent_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["intent_id"],
            ["intents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. bundle_items table
    op.create_table(
        "bundle_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("bundle_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.String(length=255), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["bundle_id"],
            ["bundles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. carts table
    op.create_table(
        "carts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("bundle_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "version", sa.Integer(), server_default="1", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'checked_out', 'abandoned')",
            name="ck_carts_status",
        ),
        sa.ForeignKeyConstraint(
            ["bundle_id"],
            ["bundles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 6. cart_items table
    op.create_table(
        "cart_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("cart_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.String(length=255), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.CheckConstraint("quantity >= 1", name="ck_cart_items_quantity"),
        sa.CheckConstraint("price >= 0.01", name="ck_cart_items_price"),
        sa.ForeignKeyConstraint(
            ["cart_id"],
            ["carts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 7. substitutions table
    op.create_table(
        "substitutions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("original_product_id", sa.String(), nullable=False),
        sa.Column("replacement_product_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "original_product_id != replacement_product_id",
            name="ck_substitution_no_self_reference",
        ),
        sa.UniqueConstraint(
            "original_product_id",
            "replacement_product_id",
            name="uq_substitution_original_replacement",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 8. user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column(
            "brand_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "category_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "reorder_affinity",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    """Drop all eight tables in reverse dependency order."""
    op.drop_table("user_preferences")
    op.drop_table("substitutions")
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("bundle_items")
    op.drop_table("bundles")
    op.drop_table("clarifications")
    op.drop_table("intents")
