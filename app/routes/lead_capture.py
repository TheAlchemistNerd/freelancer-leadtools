"""
Lead Capture Endpoints

Capture emails and track conversions from calculators.
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field

from app.repositories.lead_repository import LeadRepository, get_lead_repository

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
    calculator_result: dict | None = None
    user_type: str = Field(default="individual", description="individual or agency")
    country: str | None = None


class LeadCaptureResponse(BaseModel):
    """Lead capture response."""
    success: bool
    message: str
    next_steps: list[str]
    product_recommendation: str


class LeadAnalyticsResponse(BaseModel):
    """Lead analytics."""
    total_leads: int
    leads_by_source: dict[str, int]
    conversion_rate: float


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
    success, message = await repo.store_lead(
        email=request.email,
        source=request.source.value,
        user_type=request.user_type,
        country=request.country,
        calculator_result=request.calculator_result,
    )

    if not success:
        logger.warning(f"Lead capture suppressed/filtered: {message}")

    logger.info(f"Lead captured: {request.email} from {request.source.value}")

    # Determine product recommendation
    individual_sources = {
        LeadSource.BURNOUT, LeadSource.SKILL_GAP, LeadSource.PORTFOLIO,
        LeadSource.CLIENT_FIT, LeadSource.SCOPE_CREEP, LeadSource.HOURLY_RATE,
        LeadSource.FREELANCE_VS_FULLTIME,
    }
    agency_sources = {
        LeadSource.AGENCY_PROFIT, LeadSource.UTILIZATION, LeadSource.CLIENT_LTV,
        LeadSource.PROPOSAL_WIN_RATE, LeadSource.CASH_FLOW, LeadSource.BREAK_EVEN,
    }

    if request.source in individual_sources or request.user_type == "individual":
        product = "freelance-growth"
        product_name = "Freelance Growth OS"
    else:
        product = "freelancer-dealflow"
        product_name = "Freelance DealFlow OS"

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

    return LeadCaptureResponse(
        success=True,
        message=f"Thanks! We've sent your results to {request.email}",
        next_steps=next_steps_map.get(request.source, [
            "Check your email for detailed results",
            "Start your free trial",
            "Explore all features",
        ]),
        product_recommendation=product_name,
    )


@router.get(
    "/analytics",
    response_model=LeadAnalyticsResponse,
    summary="Lead Analytics",
    description="Get lead capture analytics directly from Redis aggregations.",
)
async def get_lead_analytics(
    repo: LeadRepository = Depends(get_lead_repository),
) -> LeadAnalyticsResponse:
    """Get lead analytics securely pulling from the LeadRepository."""
    stats = await repo.get_analytics_summary(days=30)

    return LeadAnalyticsResponse(
        total_leads=stats.get("total_leads", 0),
        leads_by_source=stats.get("leads_by_source", {}),
        conversion_rate=0.0,  # Needs unified CRM loop validation
    )


@router.post(
    "/unsubscribe/{email}",
    summary="Unsubscribe from Marketing",
    description="Remove email from marketing list.",
)
async def unsubscribe(
    email: str,
    repo: LeadRepository = Depends(get_lead_repository),
) -> dict:
    """Unsubscribe email from marketing safely."""
    # Enqueue a CRM unsubscription event
    r = await repo.get_redis()
    await r.xadd(
        repo.KEY_STREAM,
        {"email": email, "event": "unsubscribe", "timestamp": datetime.utcnow().isoformat()}
    )
    logger.info(f"Unsubscribe request dispatched to CRM queue: {email}")
    return {"success": True, "message": f"Unsubscribed {email}"}
