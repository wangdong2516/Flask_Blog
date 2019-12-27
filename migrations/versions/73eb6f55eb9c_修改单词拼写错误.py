"""修改单词拼写错误

Revision ID: 73eb6f55eb9c
Revises: a745cf195f68
Create Date: 2019-12-24 15:00:29.585507

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '73eb6f55eb9c'
down_revision = 'a745cf195f68'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.add_column('admins', sa.Column('confirmed', sa.Boolean(), nullable=False, comment='是否确认'))
    # op.drop_column('admins', 'comfirmed')
    # ### end Alembic commands ###
    pass


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('admins', sa.Column('comfirmed', mysql.TINYINT(display_width=1), server_default=sa.text("'0'"), autoincrement=False, nullable=False, comment='是否确认'))
    op.drop_column('admins', 'confirmed')
    # ### end Alembic commands ###
