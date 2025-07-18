"""Add template_theme to content table

Revision ID: add_template_theme
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_template_theme'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('content', sa.Column('template_theme', sa.String(length=50), nullable=True, default='default'))
    
    # Actualizar registros existentes con el valor por defecto
    op.execute("UPDATE content SET template_theme = 'default' WHERE template_theme IS NULL")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('content', 'template_theme')
    # ### end Alembic commands ###