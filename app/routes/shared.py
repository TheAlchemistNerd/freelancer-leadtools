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
from app.services import scenarios

router = APIRouter()


@router.post("/cost-of-living", response_model=RateCalculatorResponse,
             summary="Cost-of-living rate scenario")
@router.post(
    "/rate-ppp", deprecated=True,
    response_model=RateCalculatorResponse,
    summary="Cost-of-living rate scenario (legacy PPP URL)",
    description="Explore a user-supplied cost ratio, not official PPP or recommended market pricing.",
)
def calculate_rate_ppp(request: RateCalculatorRequest) -> RateCalculatorResponse:
    return RateCalculatorResponse(
        adjusted_rate=scenarios.cost_scenario(request.base_rate, request.cost_ratio),
        ppp_multiplier=request.cost_ratio,
        currency=request.currency,
        recommendation="Use this as a personal planning scenario, not a client-rate recommendation.",
        assumptions=["Ratio supplied by you; no country dataset is queried.",
                     "Both costs must use the same currency and period. Output stays in the input currency.",
                     "Legacy ppp_multiplier field contains your cost ratio, not verified PPP."],
        formula_version="cost-ratio-v1",
        cta={"title": "Plan a project price", "description": "Carry your assumptions into an estimate.",
             "url": settings.get_signup_url("freelancer-dealflow", "rate-ppp")},
    )



@router.post("/tax-reserve", response_model=TaxEstimatorResponse,
             summary="Tax reserve planner")
@router.post(
    "/tax-estimator", deprecated=True,
    response_model=TaxEstimatorResponse,
    summary="Tax reserve planner",
    description="Budget a reserve using your selected percentage; does not calculate statutory tax liability.",
)
def calculate_tax(request: TaxEstimatorRequest) -> TaxEstimatorResponse:
    reserve, quarterly, effective = scenarios.tax_reserve(
        request.annual_income, request.business_expenses, request.reserve_rate_percent)
    return TaxEstimatorResponse(
        estimated_tax=reserve, quarterly_payment=quarterly, effective_rate=effective,
        common_deductions=[], currency=request.currency, formula_version="tax-reserve-v1",
        assumptions=["Your reserve percentage is applied to positive income minus entered expenses.",
                     "Expenses are not verified as tax-deductible; country does not select tax rules.",
                     "Quarterly amount is one quarter of the annual reserve, not a statutory deadline or payment.",
                     "Legacy estimated_tax field is a budget reserve, not tax owed. Confirm liability with local guidance."],
        cta={"title": "Plan business cash", "description": "Keep your reserve visible in your business planning.",
             "url": settings.get_signup_url("freelancer-dealflow", "tax")},
    )



@router.post(
    "/retirement",
    response_model=RetirementPlannerResponse,
    summary="Freelancer Retirement Planner",
    description="Explore retirement funding using explicitly supplied return, inflation and withdrawal assumptions.",
)
def calculate_retirement(request: RetirementPlannerRequest) -> RetirementPlannerResponse:
    result = scenarios.retirement_scenario(
        request.current_age, request.retirement_age, request.current_retirement_savings,
        request.annual_income, request.desired_replacement_rate, request.annual_return_percent,
        request.inflation_percent, request.withdrawal_rate_percent)
    return RetirementPlannerResponse(
        **result, currency=request.currency, formula_version="retirement-real-annuity-v1",
        assumptions=["All amounts are in today's purchasing power.",
                     "Constant effective annual return and inflation; contributions at month end increase with inflation.",
                     "Target equals desired annual income divided by your withdrawal rate; that rate is not guaranteed safe.",
                     "No taxes, fees, pensions or variable-return risk modeled. Shortfall is before new contributions."],
        cta={"title": "Review your business income", "description": "Use this scenario alongside your own financial advice.",
             "url": settings.get_signup_url("freelancer-dealflow", "retirement")},
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
        roi=result["roi"],
        cta={
            "title": "Optimize Your Time",
            "description": "Track where your time goes and focus on high-value activities.",
            "url": settings.get_signup_url(product, "time-value"),
        },
    )
