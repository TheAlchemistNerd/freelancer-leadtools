"""
Shared Calculators

Free tools that appeal to both individuals and agencies.
CTAs redirect to appropriate product based on user type.

Configuration:
- Product URLs: Set FREELANCE_GROWTH_URL and FREELANCER_DEALFLOW_URL in .env
- Signup paths: Set FREELANCE_GROWTH_SIGNUP and FREELANCER_DEALFLOW_SIGNUP in .env
"""
from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.schemas import (
    RateCalculatorRequest,
    RateCalculatorResponse,
    TaxEstimatorRequest,
    TaxEstimatorResponse,
    RetirementPlannerRequest,
    RetirementPlannerResponse,
    TimeValueRequest,
    TimeValueResponse,
)
from app.services import calculators

router = APIRouter()


@router.post(
    "/rate-ppp",
    response_model=RateCalculatorResponse,
    summary="Rate Calculator with PPP Adjustment",
    description="Calculate location-adjusted rates using Purchasing Power Parity.",
)
def calculate_rate_ppp(request: RateCalculatorRequest) -> RateCalculatorResponse:
    """
    Calculate PPP-adjusted rates.

    **CTA:** Based on user type → freelance-growth or freelancer-dealflow
    """
    result = calculators.calculate_ppp_adjusted_rate(
        base_rate=request.base_rate,
        base_country=request.base_country,
        target_country=request.target_country,
        user_type=request.user_type,  # "individual" or "agency"
    )
    product = "freelance-growth" if request.user_type == "individual" else "freelancer-dealflow"
    return RateCalculatorResponse(
        adjusted_rate=result["adjusted_rate"],
        ppp_multiplier=result["ppp_multiplier"],
        local_market_rate=result["local_market_rate"],
        recommendation=result["recommendation"],
        cta={
            "title": "Track Your Rates Over Time" if request.user_type == "individual" else "Track Agency Rates",
            "description": "Monitor your rates, adjust for inflation, and stay competitive.",
            "url": settings.get_signup_url(product, "rate-ppp"),
        },
    )


@router.post(
    "/tax-estimator",
    response_model=TaxEstimatorResponse,
    summary="Freelancer Tax Estimator",
    description="Estimate quarterly taxes based on income and expenses.",
)
def calculate_tax(request: TaxEstimatorRequest) -> TaxEstimatorResponse:
    """
    Estimate quarterly taxes.

    **CTA:** "Track business expenses" → appropriate product
    """
    result = calculators.estimate_taxes(
        annual_income=request.annual_income,
        business_expenses=request.business_expenses,
        country=request.country,
        user_type=request.user_type,
    )
    product = "freelance-growth" if request.user_type == "individual" else "freelancer-dealflow"
    return TaxEstimatorResponse(
        estimated_tax=result["estimated_tax"],
        effective_rate=result["effective_rate"],
        quarterly_payment=result["quarterly_payment"],
        deductions=result["common_deductions"],
        cta={
            "title": "Track Business Expenses",
            "description": "Categorize expenses, track deductions, and prepare for tax season.",
            "url": settings.get_signup_url(product, "tax"),
        },
    )


@router.post(
    "/retirement",
    response_model=RetirementPlannerResponse,
    summary="Freelancer Retirement Planner",
    description="Plan for retirement as a self-employed professional.",
)
def calculate_retirement(request: RetirementPlannerRequest) -> RetirementPlannerResponse:
    """
    Plan retirement savings.

    **CTA:** "Plan long-term finances" → appropriate product
    """
    result = calculators.plan_retirement(
        current_age=request.current_age,
        retirement_age=request.retirement_age,
        current_savings=request.current_retirement_savings,
        annual_income=request.annual_income,
        desired_replacement_rate=request.desired_replacement_rate,
    )
    product = "freelance-growth" if request.user_type == "individual" else "freelancer-dealflow"
    return RetirementPlannerResponse(
        monthly_contribution=result["monthly_contribution"],
        annual_contribution=result["annual_contribution"],
        projected_total=result["projected_total"],
        shortfall=result["shortfall"],
        cta={
            "title": "Plan Your Financial Future",
            "description": "Track income, set aside retirement funds, and plan for the future.",
            "url": settings.get_signup_url(product, "retirement"),
        },
    )


@router.post(
    "/time-value",
    response_model=TimeValueResponse,
    summary="Time Value of Money Calculator",
    description="Calculate the opportunity cost of your time.",
)
def calculate_time_value(request: TimeValueRequest) -> TimeValueResponse:
    """
    Calculate time value.

    **CTA:** "Optimize time allocation" → appropriate product
    """
    result = calculators.calculate_time_value(
        hourly_rate=request.hourly_rate,
        task_hours=request.task_hours,
        outsourcing_cost=request.outsourcing_cost,
        user_type=request.user_type,
    )
    product = "freelance-growth" if request.user_type == "individual" else "freelancer-dealflow"
    return TimeValueResponse(
        opportunity_cost=result["opportunity_cost"],
        recommendation=result["recommendation"],
        roi_of_outsourcing=result["roi"],
        cta={
            "title": "Optimize Your Time",
            "description": "Track where your time goes and focus on high-value activities.",
            "url": settings.get_signup_url(product, "time-value"),
        },
    )
