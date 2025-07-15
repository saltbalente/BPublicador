"""add_api_key_gemini_to_users

Revision ID: 3b49011f08ff
Revises: 8029664ca447
Create Date: 2025-07-14 17:56:38.318461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b49011f08ff'
down_revision: Union[str, Sequence[str], None] = '8029664ca447'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
