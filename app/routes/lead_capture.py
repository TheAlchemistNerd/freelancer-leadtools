"""
Lead Capture Endpoints

Capture emails and track conversions from calculators.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from enum import Enum
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, model_validator

from freelancer_core.artifacts import Artifact

from app.config import settings
from app.repositories.lead_repository import (
    LeadRepository,
    LeadStoreStatus,
    get_lead_repository,
)
from app.services.action_brief import build_action_brief

logger = logging.getLogger(__name__)

router = APIRouter()


class LeadSource(str, Enum):
    """Calculator source for lead attribution."""
    BURNOUT = "burnout_calculator"
    SKILL_GAP = "skill_gap_scanner"
    PORTFOLIO = "portfolio_score"
    CLIENT_FIT = "client_fit_score"
    SCOPE_CREEP = "scope_creep_calculator"
    HOURLY_RATE = "hourly_rate_calculator"
    FREELANCE_VS_FULLTIME = "freelance_vs_fulltime"
    AGENCY_PROFIT = "agency_profit_calculator"
    UTILIZATION = "utilization_calculator"
    CLIENT_LTV = "client_ltv_calculator"
    PROPOSAL_WIN_RATE = "proposal_win_rate"
    CASH_FLOW = "cash_flow_forecast"
    BREAK_EVEN = "break_even_analysis"
    RATE_PPP = "rate_ppp_calculator"
    TAX_ESTIMATOR = "tax_estimator"
    RETIREMENT = "retirement_planner"
    TIME_VALUE = "time_value_calculator"


class LeadCaptureRequest(BaseModel):
    """Lead capture request."""
    email: EmailStr
    source: LeadSource
    calculator_result: dict[str, Any] = Field(default_factory=dict)
    user_type: Literal["individual", "agency"] = "individual"
    country: str | None = None
    email_results_consent: bool = Field(
        description="Explicit permission to process the email to deliver requested results."
    )
    marketing_consent: bool = False

    @model_validator(mode="after")
    def require_results_consent(self) -> "LeadCaptureRequest":
        if not self.email_results_consent:
            raise ValueError("email_results_consent must be true to request emailed results")
        return self


class LeadCaptureResponse(BaseModel):
    """Lead capture response."""
    success: bool
    status: LeadStoreStatus
    lead_id: str | None
    crm_queued: bool
    message: str
    next_steps: list[str]
    product_slug: str
    product_recommendation: str
    action_brief: Artifact


class LeadAnalyticsResponse(BaseModel):
    """Lead analytics."""
    total_leads: int
    leads_by_source: dict[str, int]
    conversion_rate: float | None


class ActionBriefRequest(BaseModel):
    source: LeadSource
    calculator_result: dict[str, Any] = Field(default_factory=dict)
    user_type: Literal["individual", "agency"] = "individual"


class UnsubscribeRequest(BaseModel):
    email: EmailStr
    token: str = Field(min_length=64, max_length=64)


def require_analytics_api_key(
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Keep funnel/PII-adjacent metrics out of the public calculator API."""
    if not settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics access is not configured",
        )
    if api_key is None or not any(
        hmac.compare_digest(api_key, candidate) for candidate in settings.api_keys
    ):
        raise HTTPException(status_code=403, detail="Invalid API key")


# Removed _leads mock store - Now utilizing LeadRepository with Redis backend


@router.post(
    "/capture",
    response_model=LeadCaptureResponse,
    summary="Capture Lead from Calculator",
    description="Save lead information when user submits email for results.",
)
async def capture_lead(
    request: LeadCaptureRequest,
    repo: LeadRepository = Depends(get_lead_repository),
) -> LeadCaptureResponse:
    """
    Capture lead from calculator result.
    Stores via Redis for real-time deduplication and DLQ routing.
    """
    # Persist via Repository
    result = await repo.store_lead(
        email=str(request.email),
        source=request.source.value,
        user_type=request.user_type,
        country=request.country,
        calculator_result=request.calculator_result,
        email_results_consent=request.email_results_consent,
        marketing_consent=request.marketing_consent,
    )

    logger.info(
        "Lead capture processed",
        extra={"lead_source": request.source.value, "lead_status": result.status.value},
    )

    # Personalized next steps based on source
    next_steps_map = {
        LeadSource.BURNOUT: [
            "Check your email for your 7-day recovery plan",
            "Start tracking your work hours and wellbeing",
            "Set up automated burnout check-ins",
        ],
        LeadSource.SKILL_GAP: [
            "Review your personalized skill roadmap",
            "Create your first learning goal",
            "Track progress with weekly check-ins",
        ],
        LeadSource.AGENCY_PROFIT: [
            "Connect your accounting software",
            "Set up profit margin tracking",
            "Invite your team to the dashboard",
        ],
    }

    action_brief = build_action_brief(
        source=request.source.value,
        calculator_result=request.calculator_result,
        user_type=request.user_type,
    )
    product = str(action_brief.metadata["product"])
    product_name = (
        "Freelance Growth OS"
        if product == "freelance-growth"
        else "Freelance DealFlow OS"
    )
    if result.status == LeadStoreStatus.DUPLICATE:
        message = "This result request was already recorded recently."
    elif result.crm_queued:
        message = "Your result request was recorded and queued for delivery."
    else:
        message = "Your result request was recorded; delivery is pending."

    return LeadCaptureResponse(
        success=True,
        status=result.status,
        lead_id=result.lead_id,
        crm_queued=result.crm_queued,
        message=message,
        next_steps=next_steps_map.get(request.source, [
            "Save your action brief",
            "Complete its highest-impact action",
            "Repeat the calculator and compare the result",
        ]),
        product_slug=product,
        product_recommendation=product_name,
        action_brief=action_brief,
    )


@router.post(
    "/action-brief",
    response_model=Artifact,
    summary="Create an action brief without capturing personal data",
)
async def create_action_brief(request: ActionBriefRequest) -> Artifact:
    return build_action_brief(
        source=request.source.value,
        calculator_result=request.calculator_result,
        user_type=request.user_type,
    )


@router.get(
    "/analytics",
    response_model=LeadAnalyticsResponse,
    summary="Lead Analytics",
    description="Get lead capture analytics directly from Redis aggregations.",
)
async def get_lead_analytics(
    _: None = Depends(require_analytics_api_key),
    repo: LeadRepository = Depends(get_lead_repository),
) -> LeadAnalyticsResponse:
    """Get lead analytics securely pulling from the LeadRepository."""
    stats = await repo.get_analytics_summary(days=30)

    return LeadAnalyticsResponse(
        total_leads=stats.get("total_leads", 0),
        leads_by_source=stats.get("leads_by_source", {}),
        conversion_rate=None,  # Not measured; unknown is not zero.
    )


@router.post(
    "/unsubscribe",
    summary="Unsubscribe from Marketing",
    description="Remove email from marketing list.",
)
async def unsubscribe(
    request: UnsubscribeRequest,
    repo: LeadRepository = Depends(get_lead_repository),
) -> dict:
    """Unsubscribe using the HMAC token issued in a delivery email."""
    if not settings.lead_unsubscribe_secret:
        raise HTTPException(status_code=503, detail="Unsubscribe service is not configured")
    normalized_email = str(request.email).strip().lower()
    expected = hmac.new(
        settings.lead_unsubscribe_secret.encode(),
        normalized_email.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(request.token, expected):
        raise HTTPException(status_code=403, detail="Invalid unsubscribe token")

    await repo.unsubscribe_email(normalized_email)
    logger.info("Unsubscribe request persisted")
    return {"success": True, "message": "The unsubscribe request was accepted."}
