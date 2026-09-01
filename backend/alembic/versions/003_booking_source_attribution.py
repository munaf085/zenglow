"""Booking source attribution — MARKETPLACE vs DIRECT

Revision ID: 003_booking_source
Revises: 002_verification_sm
Create Date: 2024-02-02 00:00:00.000000

Adds MARKETPLACE to AppointmentSource enum and commission tracking fields.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "003_booking_source"
down_revision: Union[str, None] = "002_verification_sm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL: add new value to existing enum
    # Must use raw SQL — ALTER TYPE cannot run inside a transaction in older PG,
    # but PG 12+ supports it outside BEGIN. Alembic handles this via execute().
    op.execute("ALTER TYPE appointmentsource ADD VALUE IF NOT EXISTS 'MARKETPLACE'")

    # Add commission tracking columns to appointments
    op.add_column("appointments", sa.Column(
        "is_marketplace_booking",
        sa.Boolean,
        nullable=False,
        server_default="false",
    ))
    op.add_column("appointments", sa.Column(
        "commission_rate",
        sa.Numeric(5, 4),
        nullable=True,
    ))
    op.add_column("appointments", sa.Column(
        "commission_amount",
        sa.Numeric(10, 2),
        nullable=True,
    ))
    op.add_column("appointments", sa.Column(
        "commission_paid",
        sa.Boolean,
        nullable=False,
        server_default="false",
    ))
    op.add_column("appointments", sa.Column(
        "is_new_customer_via_marketplace",
        sa.Boolean,
        nullable=False,
        server_default="false",
    ))

    # Index for marketplace commission reporting queries
    op.create_index(
        "ix_appointments_is_marketplace",
        "appointments",
        ["is_marketplace_booking"],
    )
    op.create_index(
        "ix_appointments_source",
        "appointments",
        ["source"],
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_source", table_name="appointments")
    op.drop_index("ix_appointments_is_marketplace", table_name="appointments")
    op.drop_column("appointments", "is_new_customer_via_marketplace")
    op.drop_column("appointments", "commission_paid")
    op.drop_column("appointments", "commission_amount")
    op.drop_column("appointments", "commission_rate")
    op.drop_column("appointments", "is_marketplace_booking")
    # Note: Cannot remove enum values in PostgreSQL — enum value stays but is unused
