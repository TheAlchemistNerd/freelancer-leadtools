from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Lead(Base):
    """Durable SQL storage for leads."""

    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, index=True, nullable=False)
    source = Column(String, index=True, nullable=False)
    user_type = Column(String, nullable=False)
    country = Column(String, default="unknown")
    calculator_result = Column(JSON, nullable=True)
    email_results_consent = Column(Integer, nullable=False, default=0)
    marketing_consent = Column(Integer, nullable=False, default=0)
    privacy_notice_version = Column(String, nullable=False, default="2026-09-01")
    ip_hash = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    synced_to_crm = Column(Integer, default=0)  # 0: pending, 1: synced, 2: failed
    synced_at = Column(DateTime(timezone=True), nullable=True)


class ReferenceDataset(Base):
    """Configuration and active version for one external reference dataset."""

    __tablename__ = "reference_datasets"

    key = Column(String(100), primary_key=True)
    provider = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    source_url = Column(Text, nullable=False)
    license_url = Column(Text, nullable=True)
    cadence = Column(String(50), nullable=False)
    max_age_days = Column(Integer, nullable=False)
    schema_version = Column(String(50), nullable=False)
    active_version = Column(String(150), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    limitation = Column(Text, nullable=False)


class ReferenceImportRun(Base):
    """Auditable result of a bounded background reference-data refresh."""

    __tablename__ = "reference_import_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_key = Column(
        String(100),
        ForeignKey("reference_datasets.key", ondelete="CASCADE"),
        nullable=False,
    )
    dataset_version = Column(String(150), nullable=True)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    records_received = Column(Integer, nullable=False, default=0)
    records_accepted = Column(Integer, nullable=False, default=0)
    checksum = Column(String(64), nullable=True)
    provider_metadata = Column(JSON, nullable=True)
    error_category = Column(String(100), nullable=True)


class ReferenceObservation(Base):
    """Immutable observation belonging to a promoted dataset version."""

    __tablename__ = "reference_observations"
    __table_args__ = (
        UniqueConstraint(
            "dataset_key",
            "dataset_version",
            "indicator_key",
            "geography_code",
            "period",
            name="uq_reference_observation_identity",
        ),
        Index(
            "ix_reference_observation_lookup",
            "dataset_key",
            "dataset_version",
            "indicator_key",
            "geography_code",
            "period",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_key = Column(
        String(100),
        ForeignKey("reference_datasets.key", ondelete="CASCADE"),
        nullable=False,
    )
    import_run_id = Column(
        String(36),
        ForeignKey("reference_import_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    dataset_version = Column(String(150), nullable=False)
    indicator_key = Column(String(100), nullable=False)
    geography_code = Column(String(10), nullable=False)
    geography_name = Column(String(255), nullable=False)
    period = Column(String(30), nullable=False)
    value = Column(Numeric(24, 8), nullable=False)
    unit = Column(String(100), nullable=False)
    observation_status = Column(String(30), nullable=True)
    source_updated_at = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), nullable=False)
