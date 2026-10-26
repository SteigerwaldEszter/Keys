"""add_is_active_to_users

Revision ID: d2dd03a367eb
Revises: e631bda97a72
Create Date: 2026-10-26 17:12:47.520950

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2dd03a367eb'
down_revision = 'e631bda97a72'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )


def downgrade():
    op.drop_column("users", "is_active")
