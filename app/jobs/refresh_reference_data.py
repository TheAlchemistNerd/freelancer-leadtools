"""Refresh versioned external reference data.

Run explicitly from the LeadTools environment:
    python -m app.jobs.refresh_reference_data

The public API never performs this provider request.
"""

from __future__ import annotations

import asyncio
import json
import sys

from app.config import settings
from app.repositories.database import SessionLocal
from app.services.reference_data import (
    ReferenceDataError,
    WorldBankProvider,
    normalize_country_codes,
    refresh_world_bank_ppp,
)


async def run() -> dict[str, object]:
    countries = normalize_country_codes(settings.reference_data_countries.split(","))
    provider = WorldBankProvider(
        timeout_seconds=settings.reference_data_timeout_seconds,
        retries=2,
    )
    with SessionLocal() as db:
        result = await refresh_world_bank_ppp(
            db,
            provider=provider,
            countries=countries,
            max_age_days=settings.reference_data_max_age_days,
        )
        return {
            "dataset": result.dataset_key,
            "version": result.dataset_version,
            "status": result.status,
            "records_received": result.records_received,
            "records_accepted": result.records_accepted,
        }


def main() -> int:
    try:
        summary = asyncio.run(run())
    except ReferenceDataError as exc:
        print(
            json.dumps({"status": "failed", "error_category": exc.category}),
            file=sys.stderr,
        )
        return 1
    except (ValueError, RuntimeError):
        print(
            json.dumps(
                {"status": "failed", "error_category": "configuration_or_runtime"}
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
