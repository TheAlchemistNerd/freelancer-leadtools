"""Read-only, last-known-good external reference data."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.repositories.database import get_db
from app.services.reference_data import (
    WORLD_BANK_INDICATOR,
    freshness_status,
    get_latest_ppp,
)


router = APIRouter()


class ReferenceProvenance(BaseModel):
    source_kind: Literal["external_reference"] = "external_reference"
    provider: str
    dataset_key: str
    dataset_version: str
    indicator: str
    source_url: str
    license_url: str | None
    retrieved_at: datetime
    source_updated_at: datetime | None
    limitation: str


class PppReferenceResponse(BaseModel):
    geography_code: str = Field(pattern=r"^[A-Z]{3}$")
    geography_name: str
    observation_period: str
    value: float
    unit: str
    observation_status: str | None
    freshness: Literal["current", "stale"]
    last_success_at: datetime
    max_age_days: int
    provenance: ReferenceProvenance


@router.get(
    "/ppp/{country_code}",
    response_model=PppReferenceResponse,
    summary="Latest verified World Bank PPP reference observation",
    description=(
        "Returns a stored last-known-good annual PPP observation. The request "
        "never calls the external provider and the value is not a market-rate "
        "or exchange-rate recommendation."
    ),
)
def ppp_reference(
    response: Response,
    country_code: str = Path(pattern=r"^[A-Za-z]{3}$"),
    db: Session = Depends(get_db),
) -> PppReferenceResponse:
    result = get_latest_ppp(db, country_code)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No verified PPP reference is available for that country.",
        )
    dataset, observation = result
    status = freshness_status(dataset)
    if status == "unavailable":
        raise HTTPException(status_code=503, detail="Reference data is unavailable.")
    response.headers["Cache-Control"] = "public, max-age=3600"
    return PppReferenceResponse(
        geography_code=observation.geography_code,
        geography_name=observation.geography_name,
        observation_period=observation.period,
        value=float(observation.value),
        unit=observation.unit,
        observation_status=observation.observation_status,
        freshness=status,
        last_success_at=dataset.last_success_at,
        max_age_days=dataset.max_age_days,
        provenance=ReferenceProvenance(
            provider=dataset.provider,
            dataset_key=dataset.key,
            dataset_version=dataset.active_version,
            indicator=WORLD_BANK_INDICATOR,
            source_url=dataset.source_url,
            license_url=dataset.license_url,
            retrieved_at=observation.retrieved_at,
            source_updated_at=observation.source_updated_at,
            limitation=dataset.limitation,
        ),
    )
