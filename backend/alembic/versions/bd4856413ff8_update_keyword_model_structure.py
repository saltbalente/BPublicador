"""Update keyword model structure

Revision ID: bd4856413ff8
Revises: 791bff3b054d
Create Date: 2025-07-11 19:16:02.008087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd4856413ff8'
down_revision: Union[str, Sequence[str], None] = '791bff3b054d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite-compatible migration: recreate table with new structure
    
    # Create new table with updated structure
    op.create_table('keywords_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='keywordstatus'), nullable=True),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='keywordpriority'), nullable=True),
        sa.Column('search_volume', sa.Integer(), nullable=True),
        sa.Column('difficulty', sa.Float(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_keywords_new_id'), 'keywords_new', ['id'], unique=False)
    op.create_index(op.f('ix_keywords_new_keyword'), 'keywords_new', ['keyword'], unique=True)
    
    # Copy data from old table to new table with status mapping
    op.execute("""
        INSERT INTO keywords_new (id, keyword, status, priority, search_volume, difficulty, category, notes, created_at, updated_at, used_at)
        SELECT 
            id, 
            keyword, 
            CASE 
                WHEN status = 'available' THEN 'PENDING'
                WHEN status = 'used' THEN 'COMPLETED'
                WHEN status = 'reserved' THEN 'PROCESSING'
                ELSE 'PENDING'
            END as status,
            'MEDIUM' as priority,
            search_volume,
            0.0 as difficulty,
            category,
            notes,
            created_at,
            updated_at,
            used_at
        FROM keywords
    """)
    
    # Drop old table and rename new table
    op.drop_table('keywords')
    op.rename_table('keywords_new', 'keywords')


def downgrade() -> None:
    """Downgrade schema."""
    # SQLite-compatible downgrade: recreate table with old structure
    
    # Create old table structure
    op.create_table('keywords_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=9), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('search_volume', sa.Integer(), nullable=True),
        sa.Column('competition', sa.String(length=20), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_keywords_old_id'), 'keywords_old', ['id'], unique=False)
    op.create_index(op.f('ix_keywords_old_keyword'), 'keywords_old', ['keyword'], unique=True)
    
    # Copy data back with reverse mapping
    op.execute("""
        INSERT INTO keywords_old (id, keyword, status, priority, search_volume, competition, category, notes, created_at, updated_at, used_at)
        SELECT 
            id, 
            keyword, 
            CASE 
                WHEN status = 'PENDING' THEN 'available'
                WHEN status = 'COMPLETED' THEN 'used'
                WHEN status = 'PROCESSING' THEN 'reserved'
                ELSE 'available'
            END as status,
            0 as priority,
            search_volume,
            'unknown' as competition,
            category,
            notes,
            created_at,
            updated_at,
            used_at
        FROM keywords
    """)
    
    # Drop new table and rename old table
    op.drop_table('keywords')
    op.rename_table('keywords_old', 'keywords')
