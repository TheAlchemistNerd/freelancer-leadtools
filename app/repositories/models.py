from sqlalchemy import Column, String, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class Lead(Base):
    """
    Durable SQL storage for leads.
    """
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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    synced_to_crm = Column(Integer, default=0)  # 0: pending, 1: synced, 2: failed
    synced_at = Column(DateTime(timezone=True), nullable=True)
