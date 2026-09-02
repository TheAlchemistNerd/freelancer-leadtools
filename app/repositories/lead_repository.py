"""
Lead Repository - Redis-backed storage for lead capture.

Architecture:
- Redis Hash for lead data
- TTL: 7 days (auto-eviction)
- Deduplication: Check email in last 24 hours
- CRM Sync: Background job via Redis Stream

Key Patterns:
- lead:{email}:{timestamp} - Lead data
- lead:emails:{email} - Deduplication check (24h TTL)
- lead:count:{source} - Analytics counter
- lead:count:{date} - Daily counter
- stream:leads - CRM sync stream
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Dict, Any, List

import redis.asyncio as redis
from redis.exceptions import RedisError
from sqlalchemy import func
from .models import Lead
from .database import SessionLocal

logger = logging.getLogger(__name__)


class LeadStoreStatus(str, Enum):
    CREATED = "created"
    DUPLICATE = "duplicate"
    DURABLE_ONLY = "durable_only"


@dataclass(frozen=True)
class LeadStoreResult:
    status: LeadStoreStatus
    lead_id: str | None
    crm_queued: bool

    @property
    def accepted(self) -> bool:
        return self.status in {LeadStoreStatus.CREATED, LeadStoreStatus.DURABLE_ONLY}


class LeadRepository:
    """
    Redis-backed repository for lead storage.
    
    Features:
    - TTL-based eviction (7 days)
    - Deduplication (24h window)
    - Analytics counters
    - CRM sync queue
    """
    
    # Key patterns
    KEY_LEAD = "lead:{email}:{timestamp}"
    KEY_DEDUPE = "lead:emails:{email}"
    KEY_COUNT_SOURCE = "lead:count:source:{source}"
    KEY_COUNT_DATE = "lead:count:date:{date}"
    KEY_SET_DATE = "lead:emails:date:{date}"
    KEY_STREAM = "stream:leads"
    
    # TTL configuration
    TTL_LEAD = 7 * 24 * 60 * 60  # 7 days in seconds
    TTL_DEDUPE = 24 * 60 * 60  # 24 hours
    TTL_ANALYTICS = 90 * 24 * 60 * 60  # 90 days
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=0.25,
                socket_timeout=0.5,
                retry_on_timeout=False,
            )
        return self._redis
    
    async def store_lead(
        self,
        email: str,
        source: str,
        user_type: str,
        country: Optional[str] = None,
        calculator_result: Optional[Dict] = None,
        email_results_consent: bool = False,
        marketing_consent: bool = False,
        privacy_notice_version: str = "2026-09-01",
        ip_hash: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LeadStoreResult:
        """
        Persist to SQL first and use Redis as an optional acceleration layer.

        Redis claims the deduplication key atomically when available. SQL is
        authoritative so a Redis outage never silently loses a lead.
        """
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        normalized_email = email.strip().lower()
        dedupe_key = self.KEY_DEDUPE.format(email=normalized_email)
        redis_client: redis.Redis | None = None
        dedupe_claimed = False

        try:
            redis_client = await self.get_redis()
            dedupe_claimed = bool(
                await redis_client.set(dedupe_key, timestamp, ex=self.TTL_DEDUPE, nx=True)
            )
            if not dedupe_claimed:
                logger.info("Duplicate lead suppressed", extra={"lead_source": source})
                return LeadStoreResult(LeadStoreStatus.DUPLICATE, None, False)
        except RedisError:
            logger.warning("Redis unavailable during lead capture; using durable storage")
            redis_client = None
        
        # Create lead data
        lead_data = {
            "email": normalized_email,
            "source": source,
            "user_type": user_type,
            "country": country or "unknown",
            "calculator_result": json.dumps(calculator_result or {}, sort_keys=True),
            "email_results_consent": "true" if email_results_consent else "false",
            "marketing_consent": "true" if marketing_consent else "false",
            "privacy_notice_version": privacy_notice_version,
            "ip_hash": ip_hash or self._hash_ip("unknown"),
            "user_agent": user_agent or "unknown",
            "created_at": timestamp,
            "synced_to_crm": "false",
        }
        
        try:
            lead_id, sql_duplicate = await asyncio.to_thread(
                self._store_in_sql, lead_data, calculator_result
            )
        except Exception:
            if redis_client is not None and dedupe_claimed:
                await redis_client.delete(dedupe_key)
            logger.exception("Durable lead persistence failed")
            raise
        if sql_duplicate:
            if redis_client is not None and dedupe_claimed:
                await redis_client.delete(dedupe_key)
            return LeadStoreResult(LeadStoreStatus.DUPLICATE, lead_id, False)

        if redis_client is None:
            logger.info("Lead stored durably", extra={"lead_source": source})
            return LeadStoreResult(LeadStoreStatus.DURABLE_ONLY, lead_id, False)

        lead_key = self.KEY_LEAD.format(
            email=hashlib.sha256(normalized_email.encode()).hexdigest()[:24],
            timestamp=now.timestamp(),
        )
        try:
            await redis_client.hset(lead_key, mapping=lead_data)
            await redis_client.expire(lead_key, self.TTL_LEAD)
            await self._update_analytics(redis_client, source, now)
            await self._queue_for_crm_sync(redis_client, lead_key, lead_data)
        except RedisError:
            logger.warning("Lead persisted but Redis enrichment/queueing failed")
            return LeadStoreResult(LeadStoreStatus.DURABLE_ONLY, lead_id, False)

        logger.info("Lead stored and queued", extra={"lead_source": source})
        return LeadStoreResult(LeadStoreStatus.CREATED, lead_id, True)

    def _store_in_sql(
        self, lead_data: Dict[str, Any], calculator_result: Optional[Dict] = None
    ) -> tuple[str | None, bool]:
        """Store a lead durably and enforce the dedupe window as a fallback."""
        with SessionLocal() as db:
            created_at = datetime.fromisoformat(lead_data["created_at"])
            cutoff = created_at - timedelta(seconds=self.TTL_DEDUPE)
            duplicate = (
                db.query(Lead.id)
                .filter(
                    func.lower(Lead.email) == lead_data["email"],
                    Lead.created_at >= cutoff,
                )
                .first()
            )
            if duplicate:
                return str(duplicate[0]), True

            lead = Lead(
                email=lead_data["email"],
                source=lead_data["source"],
                user_type=lead_data["user_type"],
                country=lead_data["country"],
                calculator_result=calculator_result,
                email_results_consent=int(
                    lead_data["email_results_consent"] == "true"
                ),
                marketing_consent=int(lead_data["marketing_consent"] == "true"),
                privacy_notice_version=lead_data["privacy_notice_version"],
                ip_hash=lead_data["ip_hash"],
                user_agent=lead_data["user_agent"],
                created_at=created_at,
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            return str(lead.id), False
    
    async def _check_duplicate(self, r: redis.Redis, email: str) -> bool:
        """Compatibility helper for callers that only need a read check."""
        dedupe_key = self.KEY_DEDUPE.format(email=email.lower())
        return await r.exists(dedupe_key)
    
    async def _update_analytics(
        self,
        r: redis.Redis,
        source: str,
        timestamp: datetime,
    ):
        """Update analytics counters."""
        # Increment source counter
        source_key = self.KEY_COUNT_SOURCE.format(source=source)
        await r.incr(source_key)
        await r.expire(source_key, self.TTL_ANALYTICS)
        
        # Increment daily counter
        date_str = timestamp.strftime("%Y-%m-%d")
        date_key = self.KEY_COUNT_DATE.format(date=date_str)
        await r.incr(date_key)
        await r.expire(date_key, self.TTL_ANALYTICS)
        
        # Add to daily set (for unique count)
        set_key = self.KEY_SET_DATE.format(date=date_str)
        await r.sadd(set_key, timestamp.isoformat())
        await r.expire(set_key, self.TTL_ANALYTICS)
    
    async def _queue_for_crm_sync(
        self,
        r: redis.Redis,
        lead_key: str,
        lead_data: Dict[str, Any],
    ):
        """Queue lead for CRM synchronization."""
        await r.xadd(
            self.KEY_STREAM,
            {
                "lead_key": lead_key,
                "email": lead_data["email"],
                "source": lead_data["source"],
                "created_at": lead_data["created_at"],
                "marketing_consent": lead_data["marketing_consent"],
                "privacy_notice_version": lead_data["privacy_notice_version"],
            },
        )
    
    def _hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy."""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    async def get_lead_count_by_source(
        self,
        source: str,
    ) -> int:
        """Get lead count for a specific source."""
        r = await self.get_redis()
        count = await r.get(self.KEY_COUNT_SOURCE.format(source=source))
        return int(count) if count else 0
    
    async def get_lead_count_by_date(
        self,
        date_str: str,
    ) -> int:
        """Get lead count for a specific date (YYYY-MM-DD)."""
        r = await self.get_redis()
        count = await r.get(self.KEY_COUNT_DATE.format(date=date_str))
        return int(count) if count else 0
    
    async def get_analytics_summary(
        self,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get analytics summary for the last N days.
        
        Returns:
            {
                "total_leads": int,
                "leads_by_source": {source: count},
                "leads_by_date": {date: count},
                "period": {start_date, end_date}
            }
        """
        r = await self.get_redis()
        now = datetime.now(timezone.utc)
        
        # Calculate date range
        start_date = now - timedelta(days=days)
        end_date = now
        
        # Get daily counts
        leads_by_date = {}
        total_leads = 0
        
        current = start_date
        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            count = await self.get_lead_count_by_date(date_str)
            leads_by_date[date_str] = count
            total_leads += count
            current += timedelta(days=1)
        
        # Get source counts (common sources)
        sources = [
            "burnout_calculator",
            "skill_gap_scanner",
            "portfolio_score",
            "client_fit_score",
            "scope_creep_calculator",
            "hourly_rate_calculator",
            "agency_profit_calculator",
            "utilization_calculator",
            "rate_ppp_calculator",
        ]
        
        leads_by_source = {}
        for source in sources:
            count = await self.get_lead_count_by_source(source)
            if count > 0:
                leads_by_source[source] = count
        
        return {
            "total_leads": total_leads,
            "leads_by_source": leads_by_source,
            "leads_by_date": leads_by_date,
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
            },
        }
    
    async def get_pending_crm_sync(
        self,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get leads pending CRM synchronization."""
        r = await self.get_redis()
        
        # Read from stream
        messages = await r.xread(
            streams={self.KEY_STREAM: "0"},
            count=count,
            block=0,  # Non-blocking
        )
        
        if not messages:
            return []
        
        leads = []
        for stream, stream_messages in messages:
            for msg_id, payload in stream_messages:
                leads.append({
                    "message_id": msg_id,
                    "lead_key": payload.get("lead_key"),
                    "email": payload.get("email"),
                    "source": payload.get("source"),
                    "created_at": payload.get("created_at"),
                })
        
        return leads
    
    async def mark_lead_synced(
        self,
        lead_key: str,
        message_id: str,
    ):
        """Mark lead as synced to CRM and remove from queue."""
        r = await self.get_redis()
        
        # Update lead
        await r.hset(lead_key, "synced_to_crm", "true")
        await r.hset(lead_key, "synced_at", datetime.now(timezone.utc).isoformat())
        
        # Acknowledge stream message
        await r.xack(self.KEY_STREAM, "crm_sync_group", message_id)

    async def unsubscribe_email(self, email: str) -> int:
        """Persist an unsubscribe before attempting optional CRM delivery."""
        normalized_email = email.strip().lower()
        updated = await asyncio.to_thread(self._persist_unsubscribe, normalized_email)

        try:
            r = await self.get_redis()
            await r.xadd(
                self.KEY_STREAM,
                {"email": normalized_email, "event": "unsubscribe"},
            )
        except RedisError:
            logger.warning("Unsubscribe persisted; CRM queue is temporarily unavailable")

        return updated

    @staticmethod
    def _persist_unsubscribe(normalized_email: str) -> int:
        with SessionLocal() as db:
            updated = (
                db.query(Lead)
                .filter(func.lower(Lead.email) == normalized_email)
                .update({Lead.marketing_consent: 0}, synchronize_session=False)
            )
            db.commit()
            return int(updated)
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Global repository instance
_lead_repository: Optional[LeadRepository] = None


def get_lead_repository(redis_url: Optional[str] = None) -> LeadRepository:
    """Get or create lead repository instance."""
    global _lead_repository
    if _lead_repository is None:
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _lead_repository = LeadRepository(redis_url)
    return _lead_repository
