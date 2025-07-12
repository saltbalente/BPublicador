"""merge heads

Revision ID: 8029664ca447
Revises: a47bf180b10b, add_template_theme
Create Date: 2025-07-12 16:34:19.906066

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8029664ca447'
down_revision: Union[str, Sequence[str], None] = ('a47bf180b10b', 'add_template_theme')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
