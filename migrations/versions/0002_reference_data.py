"""Add versioned external reference data.

Revision ID: 0002_reference_data
Revises: 0001_lead_capture
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_reference_data"
down_revision = "0001_lead_capture"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reference_datasets",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("license_url", sa.Text(), nullable=True),
        sa.Column("cadence", sa.String(length=50), nullable=False),
        sa.Column("max_age_days", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=50), nullable=False),
        sa.Column("active_version", sa.String(length=150), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("limitation", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "reference_import_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_key", sa.String(length=100), nullable=False),
        sa.Column("dataset_version", sa.String(length=150), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_received", sa.Integer(), nullable=False),
        sa.Column("records_accepted", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("provider_metadata", sa.JSON(), nullable=True),
        sa.Column("error_category", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_key"], ["reference_datasets.key"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reference_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_key", sa.String(length=100), nullable=False),
        sa.Column("import_run_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version", sa.String(length=150), nullable=False),
        sa.Column("indicator_key", sa.String(length=100), nullable=False),
        sa.Column("geography_code", sa.String(length=10), nullable=False),
        sa.Column("geography_name", sa.String(length=255), nullable=False),
        sa.Column("period", sa.String(length=30), nullable=False),
        sa.Column("value", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("unit", sa.String(length=100), nullable=False),
        sa.Column("observation_status", sa.String(length=30), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_key"], ["reference_datasets.key"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["import_run_id"], ["reference_import_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "dataset_key",
            "dataset_version",
            "indicator_key",
            "geography_code",
            "period",
            name="uq_reference_observation_identity",
        ),
    )
    op.create_index(
        "ix_reference_observation_lookup",
        "reference_observations",
        ["dataset_key", "dataset_version", "indicator_key", "geography_code", "period"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_reference_observation_lookup", table_name="reference_observations"
    )
    op.drop_table("reference_observations")
    op.drop_table("reference_import_runs")
    op.drop_table("reference_datasets")
