"""create orchestration tables

Revision ID: 78f13eb6750a
Revises: f14e53eba892
Create Date: 2026-06-09 21:46:04.808145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78f13eb6750a'
down_revision: Union[str, Sequence[str], None] = 'f14e53eba892'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This migration is a duplicate of cc023be5e56e and is made a no-op to avoid DuplicateTable errors.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

