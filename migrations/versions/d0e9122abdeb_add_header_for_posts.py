"""Add header for posts

Revision ID: d0e9122abdeb
Revises: baac018a4a8f
Create Date: 2023-11-20 16:56:50.568795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e9122abdeb'
down_revision: Union[str, None] = 'baac018a4a8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('header', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('post', 'header')
    # ### end Alembic commands ###