"""add reorder_level to items

Revision ID: 3f1c2a7b9e4d
Revises: d9d8bd9ed894
Create Date: 2026-07-19 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3f1c2a7b9e4d"
down_revision: Union[str, Sequence[str], None] = "d9d8bd9ed894"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "items",
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default=sa.text("5")),
    )
    op.alter_column("items", "reorder_level", server_default=None)


def downgrade() -> None:
    op.drop_column("items", "reorder_level")
