"""alter audit_events entity_id to uuid

Revision ID: c8946d1c5403
Revises: e09029d63af1
Create Date: 2026-06-20 09:51:09.521773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c8946d1c5403'
down_revision: Union[str, Sequence[str], None] = 'e09029d63af1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'audit_events',
        'entity_id',
        existing_type=sa.Integer(),
        type_=sa.String(length=100),
        existing_nullable=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'audit_events',
        'entity_id',
        existing_type=sa.String(length=100),
        type_=sa.Integer(),
        existing_nullable=True
    )
