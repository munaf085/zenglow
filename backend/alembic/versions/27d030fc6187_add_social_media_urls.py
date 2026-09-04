"""add social media urls

Revision ID: 27d030fc6187
Revises: 003_booking_source
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa


# Alembic revision identifiers
revision = "27d030fc6187"
down_revision = "003_booking_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "businesses",
        sa.Column(
            "instagram_url",
            sa.String(length=500),
            nullable=True,
        ),
    )

    op.add_column(
        "businesses",
        sa.Column(
            "facebook_url",
            sa.String(length=500),
            nullable=True,
        ),
    )

    op.add_column(
        "businesses",
        sa.Column(
            "tiktok_url",
            sa.String(length=500),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("businesses", "tiktok_url")
    op.drop_column("businesses", "facebook_url")
    op.drop_column("businesses", "instagram_url")