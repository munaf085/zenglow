"""Business verification state machine

Revision ID: 002_verification_sm
Revises: 001_initial_schema
Create Date: 2024-02-01 00:00:00.000000
"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "002_verification_sm"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the VerificationStatus enum
    verification_status_enum = sa.Enum(
        "NOT_APPLIED", "APPLIED", "UNDER_REVIEW", "APPROVED", "REJECTED",
        name="verificationstatus"
    )
    verification_status_enum.create(op.get_bind(), checkfirst=True)

    # Add verification columns to businesses table
    op.add_column("businesses", sa.Column(
        "verification_status",
        sa.Enum("NOT_APPLIED", "APPLIED", "UNDER_REVIEW", "APPROVED", "REJECTED",
                name="verificationstatus"),
        nullable=False,
        server_default="NOT_APPLIED",
    ))
    op.add_column("businesses", sa.Column(
        "verification_submitted_at",
        sa.DateTime(timezone=True),
        nullable=True,
    ))
    op.add_column("businesses", sa.Column(
        "verification_reviewed_at",
        sa.DateTime(timezone=True),
        nullable=True,
    ))
    op.add_column("businesses", sa.Column(
        "verification_reviewed_by_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=True,
    ))
    op.add_column("businesses", sa.Column(
        "verification_rejection_reason",
        sa.Text,
        nullable=True,
    ))
    op.add_column("businesses", sa.Column(
        "verification_notes",
        sa.Text,
        nullable=True,
    ))

    # Index for fast admin queries by verification status
    op.create_index(
        "ix_businesses_verification_status",
        "businesses",
        ["verification_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_businesses_verification_status", table_name="businesses")
    op.drop_column("businesses", "verification_notes")
    op.drop_column("businesses", "verification_rejection_reason")
    op.drop_column("businesses", "verification_reviewed_by_id")
    op.drop_column("businesses", "verification_reviewed_at")
    op.drop_column("businesses", "verification_submitted_at")
    op.drop_column("businesses", "verification_status")
    op.execute("DROP TYPE IF EXISTS verificationstatus")
