"""create community products table

Revision ID: faeabbe395e1
Revises: d12cd1a04ec2
Create Date: 2022-09-27 12:34:32.891661

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'faeabbe395e1'
down_revision = 'd12cd1a04ec2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('community_products', 
    sa.Column('product_id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('supplier', sa.String(), nullable=False),
    sa.Column('product_name', sa.String(), nullable=False),
    sa.Column('product_url', sa.String(), nullable=True),
    sa.Column('product_price', sa.Float(), nullable=False),
    sa.Column('price_by_weight', sa.String(), nullable=True),
    sa.Column('quantity', sa.Float(), nullable=False),
    sa.Column('unit', sa.String(), nullable=False),
    sa.Column('product_image', sa.String(), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False)
    )


def downgrade():
   op.drop_table('community_products')
