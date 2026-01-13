"""add invitation table

Revision ID: 13ifl2rdkxo1
Revises: u9y1le1hv8ji
Create Date: 2026-01-13 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "13ifl2rdkxo1"
down_revision: Union[str, None] = "u9y1le1hv8ji"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'invitation',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('group_id', sa.String(length=255), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('current_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=255), nullable=False, server_default='active'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index('idx_invitation_token', 'invitation', ['token'])
    op.create_index('idx_invitation_group_id', 'invitation', ['group_id'])


def downgrade() -> None:
    op.drop_index('idx_invitation_group_id', table_name='invitation')
    op.drop_index('idx_invitation_token', table_name='invitation')
    op.drop_table('invitation')
