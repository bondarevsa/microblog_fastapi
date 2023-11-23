"""Add following

Revision ID: baac018a4a8f
Revises: 3a89161e8017
Create Date: 2023-11-19 19:20:45.773691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'baac018a4a8f'
down_revision: Union[str, None] = '3a89161e8017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('following', sa.ARRAY(sa.Integer()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'following')
    # ### end Alembic commands ###