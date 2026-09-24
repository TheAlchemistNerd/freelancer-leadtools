"""
Pydantic Schemas for Freelancer LeadTools Calculators.

Organized by calculator category.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field, EmailStr, model_validator


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


# =============================================================================
# Shared CTA Schema
# =============================================================================


class CTA(BaseModel):
    """Call-to-action for calculator results."""
    title: str
    description: str
    url: str


# =============================================================================
# Individual Calculator Schemas
# =============================================================================


class BurnoutRequest(BaseModel):
    """Burnout risk calculator input."""
    weekly_hours: float = Field(ge=0, le=168, description="Average hours worked per week")
    context_switches_per_day: int = Field(ge=0, le=50, description="Average context switches per day")
    avg_sleep_hours: float = Field(ge=0, le=24, description="Average sleep hours per night")


class BurnoutResponse(BaseModel):
    """Burnout risk calculator output."""
    risk_score: float = Field(ge=0, le=100)
    risk_level: str  # "low", "medium", "high"
    recovery_plan: list[str]
    cta: CTA


class SkillGapRequest(BaseModel):
    """Skill gap scanner input."""
    target_role: str = Field(description="Target role (e.g., 'Senior Backend Developer')")
    current_skills: list[str] = Field(description="List of current skills")
    experience_level: str = Field(description="Experience level (junior, mid, senior)")
    target_skills: list[str] = Field(default_factory=list, max_length=30, description="Your explicit target capabilities; overrides the role starter template")


class SkillGapResponse(BaseModel):
    """Skill gap scanner output."""
    normalized_skills: list[str]
    gaps: list[str]
    roadmap: list[str]
    resources: list[str]
    methodology: str = "Starter checklist or user-defined targets; not a labor-market assessment."
    cta: CTA


class PortfolioRequest(BaseModel):
    """Portfolio score input."""
    github_url: Optional[str] = None
    profile_url: Optional[str] = None
    project_links: list[str] = Field(default_factory=list)


class PortfolioResponse(BaseModel):
    """Portfolio score output."""
    score: float = Field(ge=0, le=100)
    strengths: list[str]
    missing: list[str]
    improvements: list[str]
    cta: CTA


class ClientFitRequest(BaseModel):
    """Client fit score input."""
    offered_budget: float = Field(ge=0)
    proposed_timeline_days: int = Field(gt=0)
    scope_clarity_score: int = Field(ge=1, le=5)
    communication_quality_score: int = Field(ge=1, le=5)
    payment_reliability_signal: int = Field(ge=1, le=5)


class ClientFitResponse(BaseModel):
    """Client fit score output."""
    score: float = Field(ge=0, le=100)
    level: str  # "poor", "borderline", "good"
    red_flags: list[str]
    tips: list[str]
    cta: CTA


class ScopeCreepRequest(BaseModel):
    """Scope creep calculator input."""
    extra_requests_count: int = Field(ge=0)
    avg_hours_per_request: float = Field(ge=0)
    hourly_rate: float = Field(gt=0)
    delivery_delay_days: int = Field(ge=0)
    displaced_billable_hours: float = Field(ge=0, le=100000, default=0, description="Other paid work actually displaced; exclude hours already counted above")
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")


class ScopeCreepResponse(BaseModel):
    """Scope creep calculator output."""
    direct_cost: float
    delay_cost: float
    total_cost: float
    boundary_message: str
    currency: str
    assumptions: list[str]
    formula_version: str = "scope-cost-v2"
    cta: CTA


class HourlyRateRequest(BaseModel):
    """Hourly rate calculator input."""
    target_annual_income: float = Field(gt=0)
    billable_weeks_per_year: int = Field(ge=1, le=52, default=46)
    billable_hours_per_week: float = Field(ge=1, le=60, default=30)
    annual_expenses: float = Field(ge=0, default=0)
    tax_rate_percent: float = Field(ge=0, le=50, default=25)


class HourlyRateResponse(BaseModel):
    """Hourly rate calculator output."""
    hourly_rate: float
    breakdown: dict[str, float]
    market_range: dict[str, float]
    cta: CTA


class FreelanceVsFulltimeRequest(BaseModel):
    """Freelance vs full-time comparison input."""
    freelance_hourly_rate: float = Field(gt=0)
    expected_billable_hours: int = Field(ge=0, le=2080)
    fulltime_annual_salary: float = Field(gt=0)
    benefits_value: float = Field(ge=0, default=0)
    freelance_annual_expenses: float = Field(ge=0, default=0)


class FreelanceVsFulltimeResponse(BaseModel):
    """Freelance vs full-time comparison output."""
    freelance_effective: float
    fulltime_effective: float
    difference: float
    recommendation: str
    cta: CTA


# =============================================================================
# Agency Calculator Schemas
# =============================================================================


class AgencyProfitRequest(BaseModel):
    """Agency profit calculator input."""
    annual_revenue: float = Field(gt=0)
    total_salaries: float = Field(ge=0)
    annual_overhead: float = Field(ge=0)
    effective_tax_rate: float = Field(ge=0, le=50)


class AgencyProfitResponse(BaseModel):
    """Agency profit calculator output."""
    gross_profit: float
    net_profit: float
    margin_percent: float
    industry_benchmark: float | None
    cta: CTA


class UtilizationRequest(BaseModel):
    """Utilization rate calculator input."""
    total_team_size: int = Field(gt=0)
    billable_team_members: int = Field(ge=0)
    available_hours_per_week: float = Field(gt=0)
    tracked_billable_hours: float = Field(ge=0)
    target_utilization_percent: float = Field(ge=0, le=100, default=75, description="Editable planning target, not an industry benchmark")
    average_hourly_rate: float | None = Field(default=None, gt=0, le=1000000)


class UtilizationResponse(BaseModel):
    """Utilization rate calculator output."""
    utilization_percent: float
    benchmark: float
    lost_revenue: float | None
    recommendations: list[str]
    methodology: str = "Benchmark is your planning target; revenue gap assumes unused capacity could be sold at the supplied rate."
    cta: CTA


class ClientLtvRequest(BaseModel):
    """Client LTV calculator input."""
    average_project_value: float = Field(gt=0)
    projects_per_year: int = Field(ge=0)
    average_retention_years: float = Field(gt=0)
    annual_referral_value: float = Field(ge=0, default=0)


class ClientLtvResponse(BaseModel):
    """Client LTV calculator output."""
    lifetime_value: float
    annual_value: float
    referral_value: float
    cta: CTA


class ProposalWinRateRequest(BaseModel):
    """Proposal win rate calculator input."""
    proposals_sent: int = Field(gt=0)
    proposals_won: int = Field(ge=0)
    total_value_sent: float = Field(gt=0)
    total_value_won: float = Field(ge=0)

    @model_validator(mode="after")
    def wins_cannot_exceed_submissions(self):
        if self.proposals_won > self.proposals_sent or self.total_value_won > self.total_value_sent:
            raise ValueError("Wins cannot exceed submitted proposals or value")
        return self


class ProposalWinRateResponse(BaseModel):
    """Proposal win rate calculator output."""
    win_rate: float
    value_win_rate: float
    benchmark: float | None
    recommendations: list[str]
    cta: CTA


class CashFlowRequest(BaseModel):
    """Cash flow forecast input."""
    current_cash: float = Field(ge=0)
    accounts_receivable: float = Field(ge=0)
    accounts_payable: float = Field(ge=0)
    monthly_operating_expenses: float = Field(gt=0)
    expected_new_revenue: float = Field(ge=0)


class CashFlowResponse(BaseModel):
    """Cash flow forecast output."""
    forecast: list[dict[str, float]]  # 90-day forecast
    runway: float  # months
    risk_level: str  # "low", "medium", "high"
    recommendations: list[str]
    cta: CTA


class BreakEvenRequest(BaseModel):
    """Break-even analysis input."""
    monthly_fixed_costs: float = Field(gt=0)
    average_project_margin_percent: float = Field(gt=0, le=100)
    average_project_value: float | None = Field(default=None, gt=0, le=1000000000)


class BreakEvenResponse(BaseModel):
    """Break-even analysis output."""
    monthly_revenue: float
    projects_needed: float | None
    daily_revenue: float
    cta: CTA


# =============================================================================
# Shared Calculator Schemas
# =============================================================================


class RateCalculatorRequest(BaseModel):
    """PPP-adjusted rate calculator input."""
    base_rate: float = Field(gt=0, le=1000000000, description="Base hourly rate in base currency")
    cost_ratio: float = Field(gt=0, le=100, description="Target/base living-cost ratio, supplied by you; not an exchange rate")
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    base_country: str = Field(description="Base country code (ISO 3166-1 alpha-2)")
    target_country: str = Field(description="Target country code")
    user_type: str = Field(default="individual", description="individual or agency")


class RateCalculatorResponse(BaseModel):
    """PPP-adjusted rate calculator output."""
    adjusted_rate: float
    ppp_multiplier: float
    local_market_rate: float | None = None
    currency: str
    assumptions: list[str]
    formula_version: str
    recommendation: str
    cta: CTA


class TaxEstimatorRequest(BaseModel):
    """Tax estimator input."""
    annual_income: float = Field(gt=0, le=1000000000000)
    reserve_rate_percent: float = Field(ge=0, le=100)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    business_expenses: float = Field(ge=0, le=1000000000000, default=0)
    country: str = Field(description="Country code")
    user_type: str = Field(default="individual")


class TaxEstimatorResponse(BaseModel):
    """Tax estimator output."""
    estimated_tax: float
    effective_rate: float
    quarterly_payment: float
    common_deductions: list[str]
    currency: str
    assumptions: list[str]
    formula_version: str
    cta: CTA


class RetirementPlannerRequest(BaseModel):
    """Retirement planner input."""
    current_age: int = Field(ge=18, le=100)
    retirement_age: int = Field(ge=50, le=100)
    current_retirement_savings: float = Field(ge=0, le=1000000000000)
    annual_income: float = Field(gt=0, le=1000000000000)
    desired_replacement_rate: float = Field(ge=0.5, le=1.0, default=0.8)
    annual_return_percent: float = Field(ge=-50, le=50)
    inflation_percent: float = Field(ge=0, le=30)
    withdrawal_rate_percent: float = Field(ge=0.1, le=100)
    currency: str = Field(pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def retirement_must_be_future(self):
        if self.retirement_age <= self.current_age:
            raise ValueError("Retirement age must be greater than current age")
        return self


class RetirementPlannerResponse(BaseModel):
    """Retirement planner output."""
    monthly_contribution: float
    annual_contribution: float
    projected_total: float
    shortfall: float
    target_total: float
    projected_without_contributions: float
    currency: str
    assumptions: list[str]
    formula_version: str
    cta: CTA


class TimeValueRequest(BaseModel):
    """Time value calculator input."""
    hourly_rate: float = Field(gt=0)
    task_hours: float = Field(gt=0)
    outsourcing_cost: float = Field(ge=0)
    user_type: str = Field(default="individual")


class TimeValueResponse(BaseModel):
    """Time value calculator output."""
    opportunity_cost: float
    recommendation: str
    roi: float
    cta: CTA


# =============================================================================
# Lead Capture Schemas
# =============================================================================


class LeadCaptureRequest(BaseModel):
    """Lead capture input."""
    email: EmailStr
    calculator_source: str
    result_summary: Optional[str] = None


class LeadCaptureResponse(BaseModel):
    """Lead capture output."""
    success: bool
    message: str
    next_steps: list[str]
