"""
Agency Calculators

Free tools that attract agency owners.
CTAs redirect to freelancer-dealflow product.

Configuration:
- Freelancer DealFlow URL: Set FREELANCER_DEALFLOW_URL in .env
- Signup path: Set FREELANCER_DEALFLOW_SIGNUP in .env
"""
from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.schemas import (
    AgencyProfitRequest,
    AgencyProfitResponse,
    UtilizationRequest,
    UtilizationResponse,
    ClientLtvRequest,
    ClientLtvResponse,
    ProposalWinRateRequest,
    ProposalWinRateResponse,
    CashFlowRequest,
    CashFlowResponse,
    BreakEvenRequest,
    BreakEvenResponse,
)
from app.services import calculators

router = APIRouter()


@router.post(
    "/agency-profit",
    response_model=AgencyProfitResponse,
    summary="Agency Profit Margin Calculator",
    description="Calculate your agency's true profit margin after all expenses.",
)
def calculate_agency_profit(request: AgencyProfitRequest) -> AgencyProfitResponse:
    """
    Calculate agency profit margin.

    **CTA:** "Track agency finances" → freelancer-dealflow
    """
    result = calculators.calculate_agency_profit(
        revenue=request.annual_revenue,
        salaries=request.total_salaries,
        overhead=request.annual_overhead,
        taxes=request.effective_tax_rate,
    )
    return AgencyProfitResponse(
        gross_profit=result["gross_profit"],
        net_profit=result["net_profit"],
        margin_percent=result["margin_percent"],
        industry_benchmark=result["benchmark"],
        cta={
            "title": "Track Agency Finances",
            "description": "Monitor profit margins, expenses, and revenue in real-time.",
            "url": settings.get_signup_url("freelancer-dealflow", "profit-calculator"),
        },
    )


@router.post(
    "/utilization",
    response_model=UtilizationResponse,
    summary="Team Utilization Rate Calculator",
    description="Measure how effectively your team's time is being used.",
)
def calculate_utilization(request: UtilizationRequest) -> UtilizationResponse:
    """
    Calculate team utilization rate.

    **CTA:** "Optimize team capacity" → freelancer-dealflow
    """
    result = calculators.calculate_utilization(
        total_team_size=request.total_team_size,
        billable_employees=request.billable_team_members,
        available_hours=request.available_hours_per_week,
        tracked_billable=request.tracked_billable_hours,
    )
    return UtilizationResponse(
        utilization_percent=result["utilization_percent"],
        industry_benchmark=result["benchmark"],
        lost_revenue=result["lost_revenue"],
        recommendations=result["recommendations"],
        cta={
            "title": "Optimize Team Capacity",
            "description": "Track utilization, manage capacity, and maximize billable hours.",
            "url": settings.get_signup_url("freelancer-dealflow", "utilization"),
        },
    )


@router.post(
    "/client-ltv",
    response_model=ClientLtvResponse,
    summary="Client Lifetime Value Calculator",
    description="Calculate the total value of a client relationship.",
)
def calculate_client_ltv(request: ClientLtvRequest) -> ClientLtvResponse:
    """
    Calculate client lifetime value.

    **CTA:** "Manage client relationships" → freelancer-dealflow
    """
    result = calculators.calculate_client_ltv(
        avg_project_value=request.average_project_value,
        projects_per_year=request.projects_per_year,
        retention_years=request.average_retention_years,
        referral_value=request.annual_referral_value,
    )
    return ClientLtvResponse(
        lifetime_value=result["ltv"],
        annual_value=result["annual_value"],
        referral_component=result["referral_value"],
        cta={
            "title": "Manage Client Relationships",
            "description": "Track client history, identify your best clients, and nurture relationships.",
            "url": settings.get_signup_url("freelancer-dealflow", "ltv"),
        },
    )


@router.post(
    "/proposal-win-rate",
    response_model=ProposalWinRateResponse,
    summary="Proposal Win Rate Analyzer",
    description="Analyze your proposal success rate and identify improvement areas.",
)
def calculate_proposal_win_rate(request: ProposalWinRateRequest) -> ProposalWinRateResponse:
    """
    Calculate proposal win rate.

    **CTA:** "Improve proposals with AI" → freelancer-dealflow
    """
    result = calculators.calculate_proposal_win_rate(
        proposals_sent=request.proposals_sent,
        proposals_won=request.proposals_won,
        total_value_sent=request.total_value_sent,
        total_value_won=request.total_value_won,
    )
    return ProposalWinRateResponse(
        win_rate_percent=result["win_rate"],
        value_win_rate=result["value_win_rate"],
        industry_benchmark=result["benchmark"],
        recommendations=result["recommendations"],
        cta={
            "title": "Improve Proposals with AI",
            "description": "Get AI-powered proposal templates and win rate analytics.",
            "url": settings.get_signup_url("freelancer-dealflow", "proposals"),
        },
    )


@router.post(
    "/cash-flow",
    response_model=CashFlowResponse,
    summary="Cash Flow Forecast Tool",
    description="Predict your agency's cash position for the next 90 days.",
)
def calculate_cash_flow(request: CashFlowRequest) -> CashFlowResponse:
    """
    Forecast cash flow.

    **CTA:** "Manage agency finances" → freelancer-dealflow
    """
    result = calculators.forecast_cash_flow(
        current_cash=request.current_cash,
        receivables=request.accounts_receivable,
        payables=request.accounts_payable,
        monthly_burn=request.monthly_operating_expenses,
        expected_income=request.expected_new_revenue,
    )
    return CashFlowResponse(
        forecast=result["forecast"],
        runway_months=result["runway"],
        risk_level=result["risk_level"],
        recommendations=result["recommendations"],
        cta={
            "title": "Manage Agency Finances",
            "description": "Track cash flow, invoices, and expenses in real-time.",
            "url": settings.get_signup_url("freelancer-dealflow", "cash-flow"),
        },
    )


@router.post(
    "/break-even",
    response_model=BreakEvenResponse,
    summary="Break-even Analysis Calculator",
    description="Determine the minimum revenue needed to cover all costs.",
)
def calculate_break_even(request: BreakEvenRequest) -> BreakEvenResponse:
    """
    Calculate break-even point.

    **CTA:** "Track agency metrics" → freelancer-dealflow
    """
    result = calculators.calculate_break_even(
        fixed_costs=request.monthly_fixed_costs,
        avg_project_margin=request.average_project_margin_percent,
    )
    return BreakEvenResponse(
        monthly_break_even=result["monthly_revenue"],
        projects_needed=result["projects_needed"],
        daily_target=result["daily_revenue"],
        cta={
            "title": "Track Agency Metrics",
            "description": "Monitor all your agency KPIs in one dashboard.",
            "url": settings.get_signup_url("freelancer-dealflow", "break-even"),
        },
    )
