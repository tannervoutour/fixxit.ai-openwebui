"""add manager role columns to user table

Revision ID: u9y1le1hv8ji
Revises: 018012973d35
Create Date: 2026-01-13 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "u9y1le1hv8ji"
down_revision: Union[str, None] = "018012973d35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pending_group_id column for invitation system
    op.add_column(
        "user", sa.Column("pending_group_id", sa.String(), nullable=True)
    )

    # Add managed_groups column for manager role
    op.add_column(
        "user", sa.Column("managed_groups", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    # Remove columns added in upgrade
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_column("managed_groups")
        batch_op.drop_column("pending_group_id")
