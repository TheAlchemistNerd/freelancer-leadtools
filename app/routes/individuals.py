"""
Individual Freelancer Calculators

Free tools that attract individual freelancers.
CTAs redirect to freelance-growth product.

Configuration:
- Freelance Growth URL: Set FREELANCE_GROWTH_URL in .env
- Signup path: Set FREELANCE_GROWTH_SIGNUP in .env
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas import (
    BurnoutRequest,
    BurnoutResponse,
    SkillGapRequest,
    SkillGapResponse,
    PortfolioRequest,
    PortfolioResponse,
    ClientFitRequest,
    ClientFitResponse,
    ScopeCreepRequest,
    ScopeCreepResponse,
    HourlyRateRequest,
    HourlyRateResponse,
    FreelanceVsFulltimeRequest,
    FreelanceVsFulltimeResponse,
)
from app.services import calculators

router = APIRouter()


@router.post(
    "/burnout",
    response_model=BurnoutResponse,
    summary="Burnout Risk Calculator",
    description="Assess your burnout risk based on work habits, sleep, and context switching.",
)
def calculate_burnout(request: BurnoutRequest) -> BurnoutResponse:
    """
    Calculate burnout risk score.

    **Inputs:**
    - weekly_hours: Average hours worked per week
    - context_switches: Average context switches per day
    - avg_sleep_hours: Average sleep hours per night

    **Output:**
    - risk_score: 0-100 score
    - risk_level: low, medium, or high
    - recovery_plan: 7-day recovery recommendations

    **CTA:** "Get personalized coaching" → freelance-growth
    """
    result = calculators.calculate_burnout_risk(
        weekly_hours=request.weekly_hours,
        context_switches=request.context_switches_per_day,
        avg_sleep_hours=request.avg_sleep_hours,
    )
    return BurnoutResponse(
        risk_score=result["score"],
        risk_level=result["level"],
        recovery_plan=result["recovery_plan"],
        cta={
            "title": "Get Personalized Coaching",
            "description": "Track your wellbeing over time with automated check-ins and AI coaching.",
            "url": settings.get_signup_url("freelance-growth", "burnout-calculator"),
        },
    )


@router.post(
    "/skill-gap",
    response_model=SkillGapResponse,
    summary="Skill Gap Scanner",
    description="Identify skills you need to reach your target role.",
)
def calculate_skill_gap(request: SkillGapRequest) -> SkillGapResponse:
    """
    Identify skill gaps for target role.

    **CTA:** "Create learning plan" → freelance-growth SkillTree
    """
    result = calculators.calculate_skill_gap(
        target_role=request.target_role,
        current_skills=request.current_skills,
        experience_level=request.experience_level,
    )
    return SkillGapResponse(
        normalized_skills=result["normalized_skills"],
        gaps=result["gaps"],
        roadmap=result["roadmap"],
        resources=result["resources"],
        cta={
            "title": "Create Your Learning Plan",
            "description": "Track your skill development with structured goals and progress tracking.",
            "url": settings.get_signup_url("freelance-growth", "skill-gap"),
        },
    )


@router.post(
    "/portfolio",
    response_model=PortfolioResponse,
    summary="Portfolio Strength Score",
    description="Evaluate your portfolio's effectiveness.",
)
def calculate_portfolio_score(request: PortfolioRequest) -> PortfolioResponse:
    """
    Score portfolio strength.

    **CTA:** "Get improvement plan" → freelance-growth
    """
    result = calculators.calculate_portfolio_score(
        github_url=request.github_url,
        profile_url=request.profile_url,
        project_links=request.project_links,
    )
    return PortfolioResponse(
        score=result["score"],
        strengths=result["strengths"],
        missing=result["missing"],
        improvements=result["improvements"],
        cta={
            "title": "Build a Stronger Portfolio",
            "description": "Get guided projects and track your portfolio improvements.",
            "url": settings.get_signup_url("freelance-growth", "portfolio"),
        },
    )


@router.post(
    "/client-fit",
    response_model=ClientFitResponse,
    summary="Client Fit Score",
    description="Evaluate if a potential client is worth working with.",
)
def calculate_client_fit(request: ClientFitRequest) -> ClientFitResponse:
    """
    Score client fit.

    **CTA:** "Track client relationships" → freelance-growth DevLog
    """
    result = calculators.calculate_client_fit(
        offered_budget=request.offered_budget,
        timeline_days=request.proposed_timeline_days,
        scope_clarity=request.scope_clarity_score,
        communication=request.communication_quality_score,
        payment_reliability=request.payment_reliability_signal,
    )
    return ClientFitResponse(
        score=result["score"],
        level=result["level"],
        red_flags=result["red_flags"],
        tips=result["tips"],
        cta={
            "title": "Track Client Relationships",
            "description": "Log client interactions and identify patterns in your best (and worst) clients.",
            "url": settings.get_signup_url("freelance-growth", "client-fit"),
        },
    )


@router.post(
    "/scope-creep",
    response_model=ScopeCreepResponse,
    summary="Scope Creep Cost Calculator",
    description="Calculate the true cost of additional client requests.",
)
def calculate_scope_creep(request: ScopeCreepRequest) -> ScopeCreepResponse:
    """
    Calculate scope creep cost.

    **CTA:** "Set boundaries with templates" → freelance-growth
    """
    result = calculators.calculate_scope_creep(
        extra_requests=request.extra_requests_count,
        hours_per_request=request.avg_hours_per_request,
        hourly_rate=request.hourly_rate,
        delay_days=request.delivery_delay_days,
    )
    return ScopeCreepResponse(
        direct_cost=result["direct_cost"],
        delay_cost=result["delay_cost"],
        total_cost=result["total_cost"],
        boundary_message=result["boundary_message"],
        cta={
            "title": "Set Professional Boundaries",
            "description": "Get templates for change orders, boundary setting, and client communication.",
            "url": settings.get_signup_url("freelance-growth", "scope-creep"),
        },
    )


@router.post(
    "/hourly-rate",
    response_model=HourlyRateResponse,
    summary="Hourly Rate Calculator",
    description="Determine your optimal hourly rate based on income goals.",
)
def calculate_hourly_rate(request: HourlyRateRequest) -> HourlyRateResponse:
    """
    Calculate optimal hourly rate.

    **CTA:** "Track time effectively" → freelance-growth TimeBank
    """
    result = calculators.calculate_hourly_rate(
        target_annual_income=request.target_annual_income,
        billable_weeks=request.billable_weeks_per_year,
        billable_hours=request.billable_hours_per_week,
        expenses=request.annual_expenses,
        taxes=request.tax_rate_percent,
    )
    return HourlyRateResponse(
        hourly_rate=result["hourly_rate"],
        breakdown=result["breakdown"],
        market_range=result["market_range"],
        cta={
            "title": "Track Your Time",
            "description": "Accurately track billable hours and ensure you're meeting your rate targets.",
            "url": settings.get_signup_url("freelance-growth", "rate-calculator"),
        },
    )


@router.post(
    "/freelance-vs-fulltime",
    response_model=FreelanceVsFulltimeResponse,
    summary="Freelance vs Full-time ROI Calculator",
    description="Compare the true earnings of freelancing vs full-time employment.",
)
def calculate_freelance_vs_fulltime(request: FreelanceVsFulltimeRequest) -> FreelanceVsFulltimeResponse:
    """
    Compare freelance vs full-time earnings.

    **CTA:** "Manage freelance finances" → freelance-growth
    """
    result = calculators.compare_freelance_vs_fulltime(
        freelance_rate=request.freelance_hourly_rate,
        freelance_hours=request.expected_billable_hours,
        fulltime_salary=request.fulltime_annual_salary,
        benefits_value=request.benefits_value,
        freelance_expenses=request.freelance_annual_expenses,
    )
    return FreelanceVsFulltimeResponse(
        freelance_effective=result["freelance_effective"],
        fulltime_effective=result["fulltime_effective"],
        difference=result["difference"],
        recommendation=result["recommendation"],
        cta={
            "title": "Manage Your Freelance Business",
            "description": "Track income, expenses, and taxes all in one place.",
            "url": settings.get_signup_url("freelance-growth", "freelance-vs-fulltime"),
        },
    )
