from datetime import datetime, timedelta, timezone
from decimal import Decimal
import asyncio

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.repositories.database import get_db
from app.repositories.models import (
    Base,
    ReferenceDataset,
    ReferenceImportRun,
    ReferenceObservation,
)
from app.routes.reference_data import router
from app.services.reference_data import (
    ProviderBatch,
    PppObservation,
    ReferenceDataError,
    WORLD_BANK_DATASET_KEY,
    WorldBankProvider,
    get_latest_ppp,
    refresh_world_bank_ppp,
)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


def batch(value: str = "45.125") -> ProviderBatch:
    return ProviderBatch(
        records_received=3,
        observations=(
            PppObservation(
                geography_code="KEN",
                geography_name="Kenya",
                period="2023",
                value=Decimal("44.25"),
                observation_status=None,
            ),
            PppObservation(
                geography_code="KEN",
                geography_name="Kenya",
                period="2024",
                value=Decimal(value),
                observation_status="E",
            ),
        ),
        source_updated_at=datetime(2026, 5, 27, tzinfo=timezone.utc),
        metadata={
            "last_updated": "2026-05-27",
            "page": 1,
            "pages": 1,
            "source_id": "2",
        },
    )


class StubProvider:
    def __init__(self, result=None, failure=None):
        self.result = result or batch()
        self.failure = failure
        self.calls = []

    async def fetch_ppp(self, countries):
        self.calls.append(tuple(countries))
        if self.failure:
            raise self.failure
        return self.result


def test_provider_parses_valid_rows_and_retries_server_error():
    payload = [
        {"page": 1, "pages": 1, "sourceid": "2", "lastupdated": "2026-05-27"},
        [
            {
                "country": {"id": "KE", "value": "Kenya"},
                "countryiso3code": "KEN",
                "date": "2024",
                "value": 45.125,
                "obs_status": "E",
            },
            {
                "country": {"id": "KE", "value": "Kenya"},
                "countryiso3code": "KEN",
                "date": "2023",
                "value": None,
                "obs_status": "",
            },
        ],
    ]
    attempts = 0

    def handler(request):
        nonlocal attempts
        attempts += 1
        assert request.url.host == "api.worldbank.org"
        assert "/indicator/PA.NUS.PPP" in request.url.path
        if attempts == 1:
            return httpx.Response(503, json={"message": "temporary"})
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)

    async def exercise():
        async with httpx.AsyncClient(
            transport=transport, base_url="https://api.worldbank.org/v2"
        ) as client:
            provider = WorldBankProvider(client=client, retries=1)
            return await provider.fetch_ppp(["ken"])

    result = asyncio.run(exercise())
    assert attempts == 2
    assert result.records_received == 2
    assert result.source_updated_at == datetime(2026, 5, 27, tzinfo=timezone.utc)
    assert result.observations == (
        PppObservation("KEN", "Kenya", "2024", Decimal("45.125"), "E"),
    )


@pytest.mark.parametrize(
    "value,category",
    [(0, "invalid_value"), ("NaN", "invalid_value")],
)
def test_provider_rejects_invalid_non_null_observations(value, category):
    payload = [
        {"page": 1, "pages": 1, "lastupdated": "2026-05-27"},
        [
            {
                "country": {"value": "Kenya"},
                "countryiso3code": "KEN",
                "date": "2024",
                "value": value,
            }
        ],
    ]

    async def exercise():
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json=payload)
        )
        async with httpx.AsyncClient(
            transport=transport, base_url="https://api.worldbank.org/v2"
        ) as client:
            return await WorldBankProvider(client=client).fetch_ppp(["KEN"])

    with pytest.raises(ReferenceDataError) as exc:
        asyncio.run(exercise())
    assert exc.value.category == category


def test_refresh_promotes_complete_version_and_is_idempotent(db):
    provider = StubProvider()
    first = asyncio.run(
        refresh_world_bank_ppp(
            db, provider=provider, countries=["KEN"], max_age_days=500
        )
    )
    second = asyncio.run(
        refresh_world_bank_ppp(
            db, provider=provider, countries=["KEN"], max_age_days=500
        )
    )

    dataset = db.get(ReferenceDataset, WORLD_BANK_DATASET_KEY)
    assert first.status == second.status == "succeeded"
    assert dataset.active_version == first.dataset_version == second.dataset_version
    assert db.scalar(select(func.count()).select_from(ReferenceObservation)) == 2
    assert db.scalar(select(func.count()).select_from(ReferenceImportRun)) == 2
    assert get_latest_ppp(db, "ken")[1].period == "2024"


def test_failed_refresh_preserves_last_known_good_version(db):
    success = asyncio.run(
        refresh_world_bank_ppp(
            db,
            provider=StubProvider(),
            countries=["KEN"],
            max_age_days=500,
        )
    )
    before_count = db.scalar(select(func.count()).select_from(ReferenceObservation))
    failure = ReferenceDataError("provider_timeout", "safe failure")

    with pytest.raises(ReferenceDataError):
        asyncio.run(
            refresh_world_bank_ppp(
                db,
                provider=StubProvider(failure=failure),
                countries=["KEN"],
                max_age_days=500,
            )
        )

    dataset = db.get(ReferenceDataset, WORLD_BANK_DATASET_KEY)
    failed = db.scalar(
        select(ReferenceImportRun)
        .where(ReferenceImportRun.status == "failed")
        .order_by(ReferenceImportRun.started_at.desc())
    )
    assert dataset.active_version == success.dataset_version
    assert (
        db.scalar(select(func.count()).select_from(ReferenceObservation))
        == before_count
    )
    assert failed.error_category == "provider_timeout"


def test_read_api_returns_provenance_and_staleness(db):
    asyncio.run(
        refresh_world_bank_ppp(
            db,
            provider=StubProvider(),
            countries=["KEN"],
            max_age_days=500,
        )
    )
    dataset = db.get(ReferenceDataset, WORLD_BANK_DATASET_KEY)
    dataset.last_success_at = datetime.now(timezone.utc) - timedelta(days=501)
    db.commit()

    app = FastAPI()
    app.include_router(router, prefix="/reference-data")

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        response = client.get("/reference-data/ppp/ken")
        missing = client.get("/reference-data/ppp/usa")
        invalid = client.get("/reference-data/ppp/not-a-code")

    assert response.status_code == 200
    body = response.json()
    assert body["geography_code"] == "KEN"
    assert body["observation_period"] == "2024"
    assert body["freshness"] == "stale"
    assert body["provenance"]["dataset_key"] == "world-bank-ppp"
    assert body["provenance"]["indicator"] == "PA.NUS.PPP"
    assert "market rate" in body["provenance"]["limitation"]
    assert response.headers["cache-control"] == "public, max-age=3600"
    assert missing.status_code == 404
    assert invalid.status_code == 422
