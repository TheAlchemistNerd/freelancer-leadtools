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

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

import redis.asyncio as redis

logger = logging.getLogger(__name__)


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
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
        return self._redis
    
    async def store_lead(
        self,
        email: str,
        source: str,
        user_type: str,
        country: Optional[str] = None,
        calculator_result: Optional[Dict] = None,
        ip_hash: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Store lead in Redis with deduplication.
        
        Returns:
            (is_new_lead, message)
            - is_new_lead: True if this is a new lead (not duplicate)
            - message: Status message
        """
        r = await self.get_redis()
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        
        # Check for duplicate (email submitted in last 24h)
        is_duplicate = await self._check_duplicate(r, email)
        if is_duplicate:
            logger.info(f"Duplicate lead suppressed: {email}")
            return False, "Lead already captured in last 24 hours"
        
        # Create lead data
        lead_data = {
            "email": email,
            "source": source,
            "user_type": user_type,
            "country": country or "unknown",
            "calculator_result": json.dumps(calculator_result) if calculator_result else None,
            "ip_hash": ip_hash or self._hash_ip("unknown"),
            "user_agent": user_agent or "unknown",
            "created_at": timestamp,
            "synced_to_crm": "false",
        }
        
        # Store lead with TTL
        lead_key = self.KEY_LEAD.format(email=email.lower(), timestamp=now.timestamp())
        await r.hset(lead_key, mapping=lead_data)
        await r.expire(lead_key, self.TTL_LEAD)
        
        # Set deduplication flag
        dedupe_key = self.KEY_DEDUPE.format(email=email.lower())
        await r.set(dedupe_key, timestamp, ex=self.TTL_DEDUPE)
        
        # Update analytics counters
        await self._update_analytics(r, source, now)
        
        # Queue for CRM sync
        await self._queue_for_crm_sync(r, lead_key, lead_data)
        
        logger.info(f"Lead stored: {email} from {source}")
        return True, "Lead captured successfully"
    
    async def _check_duplicate(self, r: redis.Redis, email: str) -> bool:
        """Check if email was submitted in last 24 hours."""
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
