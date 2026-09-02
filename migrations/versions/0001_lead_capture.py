"""Create durable, consent-aware lead capture.

Revision ID: 0001_lead_capture
Revises: None
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_lead_capture"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("user_type", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("calculator_result", sa.JSON(), nullable=True),
        sa.Column("email_results_consent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("marketing_consent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "privacy_notice_version", sa.String(), nullable=False, server_default="2026-09-01"
        ),
        sa.Column("ip_hash", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("synced_to_crm", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leads_email", "leads", ["email"])
    op.create_index("ix_leads_source", "leads", ["source"])
    op.create_index("ix_leads_created_at", "leads", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_leads_created_at", table_name="leads")
    op.drop_index("ix_leads_source", table_name="leads")
    op.drop_index("ix_leads_email", table_name="leads")
    op.drop_table("leads")
