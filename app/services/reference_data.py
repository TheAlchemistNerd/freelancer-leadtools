"""Versioned, last-known-good reference data for public calculator context."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any, Iterable
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repositories.models import (
    ReferenceDataset,
    ReferenceImportRun,
    ReferenceObservation,
)


WORLD_BANK_DATASET_KEY = "world-bank-ppp"
WORLD_BANK_INDICATOR = "PA.NUS.PPP"
WORLD_BANK_API_ROOT = "https://api.worldbank.org/v2"
WORLD_BANK_SOURCE_URL = (
    "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392"
)
WORLD_BANK_LICENSE_URL = (
    "https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets"
)
WORLD_BANK_LIMITATION = (
    "Annual purchasing-power context only. It is not a current exchange rate, "
    "freelancer market rate, tax rule, or client-price recommendation."
)
MAX_PROVIDER_BYTES = 2_000_000
MAX_COUNTRIES_PER_IMPORT = 50
COUNTRY_CODE = re.compile(r"^[A-Z]{3}$")


class ReferenceDataError(RuntimeError):
    """Safe, categorized refresh failure."""

    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


@dataclass(frozen=True)
class PppObservation:
    geography_code: str
    geography_name: str
    period: str
    value: Decimal
    observation_status: str | None


@dataclass(frozen=True)
class ProviderBatch:
    records_received: int
    observations: tuple[PppObservation, ...]
    source_updated_at: datetime | None
    metadata: dict[str, Any]


def normalize_country_codes(countries: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(
        dict.fromkeys(code.strip().upper() for code in countries if code.strip())
    )
    if not normalized:
        raise ValueError("At least one ISO 3166-1 alpha-3 country code is required")
    if len(normalized) > MAX_COUNTRIES_PER_IMPORT:
        raise ValueError(
            f"At most {MAX_COUNTRIES_PER_IMPORT} countries may be refreshed"
        )
    if any(not COUNTRY_CODE.fullmatch(code) for code in normalized):
        raise ValueError("Country codes must be three uppercase ASCII letters")
    return normalized


class WorldBankProvider:
    """Bounded client for the fixed World Bank Indicators API host."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 20.0,
        retries: int = 2,
        client: httpx.AsyncClient | None = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.client = client

    async def fetch_ppp(self, countries: Iterable[str]) -> ProviderBatch:
        country_codes = normalize_country_codes(countries)
        current_year = datetime.now(timezone.utc).year
        path = f"/country/{';'.join(country_codes)}/indicator/{WORLD_BANK_INDICATOR}"
        params = {
            "format": "json",
            "per_page": "1000",
            "date": f"{current_year - 8}:{current_year}",
        }

        if self.client is not None:
            response = await self._request(self.client, path, params)
        else:
            timeout = httpx.Timeout(self.timeout_seconds)
            async with httpx.AsyncClient(
                base_url=WORLD_BANK_API_ROOT,
                timeout=timeout,
                follow_redirects=False,
                trust_env=False,
                headers={"Accept": "application/json"},
            ) as client:
                response = await self._request(client, path, params)

        if len(response.content) > MAX_PROVIDER_BYTES:
            raise ReferenceDataError(
                "payload_too_large", "Provider response exceeded limit"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ReferenceDataError(
                "invalid_json", "Provider returned invalid JSON"
            ) from exc
        return self._parse(payload, set(country_codes))

    async def _request(
        self, client: httpx.AsyncClient, path: str, params: dict[str, str]
    ) -> httpx.Response:
        for attempt in range(self.retries + 1):
            try:
                response = await client.get(path, params=params)
                if 500 <= response.status_code <= 599:
                    raise ReferenceDataError(
                        "provider_unavailable", "Provider returned a server error"
                    )
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                failure = ReferenceDataError(
                    "provider_timeout", "Provider could not be reached within the limit"
                )
                if attempt == self.retries:
                    raise failure from exc
            except httpx.HTTPStatusError as exc:
                raise ReferenceDataError(
                    "provider_http_error", "Provider rejected the request"
                ) from exc
            except ReferenceDataError:
                if attempt == self.retries:
                    raise
            await asyncio.sleep(0.25 * (2**attempt))
        raise ReferenceDataError("provider_unavailable", "Provider request failed")

    @staticmethod
    def _parse(payload: Any, expected_countries: set[str]) -> ProviderBatch:
        if (
            not isinstance(payload, list)
            or len(payload) != 2
            or not isinstance(payload[0], dict)
            or not isinstance(payload[1], list)
        ):
            raise ReferenceDataError(
                "invalid_schema", "Unexpected provider response shape"
            )

        metadata, rows = payload
        source_updated_at = _parse_provider_date(metadata.get("lastupdated"))
        observations: list[PppObservation] = []
        seen: set[tuple[str, str]] = set()

        for row in rows:
            if not isinstance(row, dict):
                raise ReferenceDataError(
                    "invalid_schema", "Observation is not an object"
                )
            value = row.get("value")
            if value is None:
                continue
            code = str(row.get("countryiso3code", "")).upper()
            period = str(row.get("date", ""))
            country = row.get("country")
            country_name = country.get("value") if isinstance(country, dict) else None
            if (
                code not in expected_countries
                or not re.fullmatch(r"\d{4}", period)
                or not isinstance(country_name, str)
                or not country_name.strip()
            ):
                raise ReferenceDataError(
                    "invalid_schema", "Invalid observation identity"
                )
            try:
                decimal_value = Decimal(str(value))
            except InvalidOperation as exc:
                raise ReferenceDataError(
                    "invalid_value", "Observation is not numeric"
                ) from exc
            if not decimal_value.is_finite() or decimal_value <= 0:
                raise ReferenceDataError(
                    "invalid_value", "PPP observation must be positive"
                )
            identity = (code, period)
            if identity in seen:
                raise ReferenceDataError(
                    "duplicate_observation", "Duplicate observation"
                )
            seen.add(identity)
            status = row.get("obs_status")
            observations.append(
                PppObservation(
                    geography_code=code,
                    geography_name=country_name.strip(),
                    period=period,
                    value=decimal_value,
                    observation_status=str(status) if status else None,
                )
            )

        if not observations:
            raise ReferenceDataError("empty_dataset", "No usable observations returned")
        observations.sort(key=lambda item: (item.geography_code, item.period))
        safe_metadata = {
            "last_updated": metadata.get("lastupdated"),
            "page": metadata.get("page"),
            "pages": metadata.get("pages"),
            "source_id": metadata.get("sourceid"),
        }
        return ProviderBatch(
            records_received=len(rows),
            observations=tuple(observations),
            source_updated_at=source_updated_at,
            metadata=safe_metadata,
        )


def _parse_provider_date(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ReferenceDataError(
            "invalid_schema", "Invalid provider update date"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ensure_dataset(db: Session, max_age_days: int) -> ReferenceDataset:
    dataset = db.get(ReferenceDataset, WORLD_BANK_DATASET_KEY)
    if dataset is None:
        dataset = ReferenceDataset(key=WORLD_BANK_DATASET_KEY)
        db.add(dataset)
    dataset.provider = "World Bank"
    dataset.title = "PPP conversion factor, GDP"
    dataset.source_url = WORLD_BANK_SOURCE_URL
    dataset.license_url = WORLD_BANK_LICENSE_URL
    dataset.cadence = "annual"
    dataset.max_age_days = max_age_days
    dataset.schema_version = "world-bank-ppp-v1"
    dataset.limitation = WORLD_BANK_LIMITATION
    return dataset


def _checksum(batch: ProviderBatch) -> str:
    canonical = [
        {
            "country": item.geography_code,
            "name": item.geography_name,
            "period": item.period,
            "value": format(item.value, "f"),
            "status": item.observation_status,
        }
        for item in batch.observations
    ]
    encoded = json.dumps(
        canonical, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _version_for(batch: ProviderBatch, checksum: str) -> str:
    updated = (
        batch.source_updated_at.date().isoformat()
        if batch.source_updated_at
        else "unknown-date"
    )
    return f"world-bank-ppp-v1-{updated}-{checksum[:12]}"


async def refresh_world_bank_ppp(
    db: Session,
    *,
    provider: WorldBankProvider,
    countries: Iterable[str],
    max_age_days: int,
) -> ReferenceImportRun:
    """Refresh PPP snapshots and promote them only after a complete valid import."""

    country_codes = normalize_country_codes(countries)
    now = datetime.now(timezone.utc)
    dataset = _ensure_dataset(db, max_age_days)
    run = ReferenceImportRun(
        id=str(uuid4()),
        dataset_key=WORLD_BANK_DATASET_KEY,
        status="started",
        started_at=now,
        records_received=0,
        records_accepted=0,
    )
    db.add(run)
    db.commit()

    try:
        batch = await provider.fetch_ppp(country_codes)
        checksum = _checksum(batch)
        version = _version_for(batch, checksum)

        dataset = db.get(ReferenceDataset, WORLD_BANK_DATASET_KEY)
        run = db.get(ReferenceImportRun, run.id)
        existing = db.scalar(
            select(ReferenceObservation.id)
            .where(
                ReferenceObservation.dataset_key == WORLD_BANK_DATASET_KEY,
                ReferenceObservation.dataset_version == version,
            )
            .limit(1)
        )
        if existing is None:
            retrieved_at = datetime.now(timezone.utc)
            db.add_all(
                [
                    ReferenceObservation(
                        id=str(uuid4()),
                        dataset_key=WORLD_BANK_DATASET_KEY,
                        import_run_id=run.id,
                        dataset_version=version,
                        indicator_key=WORLD_BANK_INDICATOR,
                        geography_code=item.geography_code,
                        geography_name=item.geography_name,
                        period=item.period,
                        value=item.value,
                        unit="local currency units per international dollar",
                        observation_status=item.observation_status,
                        source_updated_at=batch.source_updated_at,
                        retrieved_at=retrieved_at,
                    )
                    for item in batch.observations
                ]
            )

        finished_at = datetime.now(timezone.utc)
        dataset.active_version = version
        dataset.last_success_at = finished_at
        run.dataset_version = version
        run.status = "succeeded"
        run.finished_at = finished_at
        run.records_received = batch.records_received
        run.records_accepted = len(batch.observations)
        run.checksum = checksum
        run.provider_metadata = batch.metadata
        run.error_category = None
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:
        db.rollback()
        failed_run = db.get(ReferenceImportRun, run.id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.finished_at = datetime.now(timezone.utc)
            failed_run.error_category = (
                exc.category
                if isinstance(exc, ReferenceDataError)
                else "internal_error"
            )
            db.commit()
        raise


def get_latest_ppp(
    db: Session, country_code: str
) -> tuple[ReferenceDataset, ReferenceObservation] | None:
    code = normalize_country_codes((country_code,))[0]
    dataset = db.get(ReferenceDataset, WORLD_BANK_DATASET_KEY)
    if dataset is None or not dataset.active_version:
        return None
    observation = db.scalar(
        select(ReferenceObservation)
        .where(
            ReferenceObservation.dataset_key == dataset.key,
            ReferenceObservation.dataset_version == dataset.active_version,
            ReferenceObservation.indicator_key == WORLD_BANK_INDICATOR,
            ReferenceObservation.geography_code == code,
        )
        .order_by(ReferenceObservation.period.desc())
        .limit(1)
    )
    if observation is None:
        return None
    return dataset, observation


def freshness_status(dataset: ReferenceDataset, *, now: datetime | None = None) -> str:
    if dataset.last_success_at is None:
        return "unavailable"
    checked_at = dataset.last_success_at
    if checked_at.tzinfo is None:
        checked_at = checked_at.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return (
        "stale"
        if current - checked_at.astimezone(timezone.utc)
        > timedelta(days=dataset.max_age_days)
        else "current"
    )
