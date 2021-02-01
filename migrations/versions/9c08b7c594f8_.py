"""empty message

Revision ID: 9c08b7c594f8
Revises: 61e05a93ffe6
Create Date: 2021-02-01 19:59:34.392297

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c08b7c594f8'
down_revision = '61e05a93ffe6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('images', sa.Column('dataset_id', sa.Integer(), nullable=True))
    op.add_column('images', sa.Column('label', sa.String(), nullable=True))
    op.add_column('images', sa.Column('labelled', sa.Boolean(), nullable=True))
    op.add_column('images', sa.Column('labelled_by', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'images', 'users', ['labelled_by'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'images', 'datasets', ['dataset_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'images', type_='foreignkey')
    op.drop_constraint(None, 'images', type_='foreignkey')
    op.drop_column('images', 'labelled_by')
    op.drop_column('images', 'labelled')
    op.drop_column('images', 'label')
    op.drop_column('images', 'dataset_id')
    # ### end Alembic commands ###