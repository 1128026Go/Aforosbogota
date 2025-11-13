"""baseline

Revision ID: 0001_baseline
Revises: 
Create Date: 2025-11-11 22:10:00.000000

"""
from __future__ import annotations

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Empty baseline; run `alembic revision --autogenerate` to create real migrations
    pass


def downgrade() -> None:
    pass
