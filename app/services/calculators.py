"""
Calculator Services for Freelancer LeadTools.

Core calculation logic for all free calculators.
"""
from __future__ import annotations

from typing import Optional


# =============================================================================
# Individual Calculator Functions
# =============================================================================


def calculate_burnout_risk(
    weekly_hours: float,
    context_switches: int,
    avg_sleep_hours: float,
) -> dict:
    """
    Calculate burnout risk score.

    Algorithm:
    - Overtime component: hours beyond 35/week
    - Context switching: mental load from interruptions
    - Sleep debt: cognitive impairment from poor sleep
    """
    # Overtime component (0-40 points)
    overtime = max(0, weekly_hours - 35)
    overtime_score = min(40, overtime * 1.5)

    # Context switching component (0-30 points)
    switching_score = min(30, context_switches * 2)

    # Sleep debt component (0-30 points)
    sleep_debt = max(0, 7.5 - avg_sleep_hours)
    sleep_score = min(30, sleep_debt * 10)

    # Total score
    total_score = min(100, overtime_score + switching_score + sleep_score)

    # Risk level
    if total_score >= 70:
        level = "high"
    elif total_score >= 40:
        level = "medium"
    else:
        level = "low"

    # Recovery plan
    recovery_plan = [
        "Day 1: Reduce workload by 20%, remove one non-essential meeting",
        "Day 2: Schedule 90-minute deep work block, one recovery break",
        "Day 3: Cap context switching by batching communication",
        "Day 4: Prioritize top 3 tasks only, defer low-impact work",
        "Day 5: End work 60 minutes early, review stress triggers",
        "Day 6: No backlog catch-up, only maintenance and planning",
        "Day 7: Weekly reset, plan sustainable hours for next week",
    ]

    return {
        "score": round(total_score, 2),
        "level": level,
        "recovery_plan": recovery_plan,
    }


def calculate_skill_gap(
    target_role: str,
    current_skills: list[str],
    experience_level: str,
) -> dict:
    """
    Identify skill gaps for target role.

    Uses predefined skill templates for common roles.
    """
    # Skill templates for common roles
    templates = {
        "backend": ["python", "apis", "sql", "testing", "docker", "aws", "caching"],
        "frontend": ["javascript", "react", "css", "testing", "performance", "accessibility"],
        "fullstack": ["python", "javascript", "apis", "sql", "testing", "docker", "react"],
        "devops": ["docker", "kubernetes", "ci/cd", "aws", "monitoring", "terraform"],
        "data": ["python", "sql", "statistics", "ml", "visualization", "pandas"],
    }

    # Find matching template
    target_lower = target_role.lower()
    matched_skills = []
    for role, skills in templates.items():
        if role in target_lower:
            matched_skills = skills
            break

    if not matched_skills:
        matched_skills = templates["fullstack"]  # Default

    # Normalize current skills
    normalized = [s.lower().strip() for s in current_skills]

    # Find gaps
    gaps = [s for s in matched_skills if s not in normalized]

    # Generate roadmap based on experience level
    if experience_level.lower() == "junior":
        roadmap = [
            "30 days: Master 2-3 foundational skills from gaps",
            "60 days: Build one project using new skills",
            "90 days: Contribute to open source or freelance project",
        ]
    elif experience_level.lower() == "senior":
        roadmap = [
            "30 days: Deep dive into architecture patterns",
            "60 days: Lead a complex project end-to-end",
            "90 days: Mentor others and document learnings",
        ]
    else:  # mid
        roadmap = [
            "30 days: Close 1-2 key skill gaps",
            "60 days: Ship one portfolio project",
            "90 days: Document outcomes, apply to client work",
        ]

    # Suggested resources
    resources = [f"https://example.com/learn/{gap}" for gap in gaps[:4]]

    return {
        "normalized_skills": sorted(normalized),
        "gaps": gaps,
        "roadmap": roadmap,
        "resources": resources,
    }


def calculate_portfolio_score(
    github_url: Optional[str],
    profile_url: Optional[str],
    project_links: list[str],
) -> dict:
    """
    Score portfolio strength.

    Factors:
    - Code visibility (GitHub)
    - Professional presence (profile)
    - Project quantity and quality
    """
    score = 40.0  # Base score

    strengths = []
    missing = []
    improvements = []

    # GitHub presence (+20)
    if github_url:
        score += 20
        strengths.append("Visible code repositories")
    else:
        missing.append("GitHub or code repository")

    # Professional profile (+10)
    if profile_url:
        score += 10
        strengths.append("Professional online presence")
    else:
        missing.append("Professional portfolio website")

    # Project links (+6 each, max 30)
    project_count = min(5, len(project_links))
    score += project_count * 6

    if project_count >= 3:
        strengths.append("Multiple portfolio projects")
    else:
        missing.append("More portfolio projects (aim for 3+)")

    # Common improvements
    improvements = [
        "Add case studies with business outcomes",
        "Include before/after metrics",
        "Add client testimonials if available",
        "Document technical architecture decisions",
        "Pin strongest repositories on GitHub",
    ]

    return {
        "score": min(100, round(score, 2)),
        "strengths": strengths,
        "missing": missing,
        "improvements": improvements[:3],
    }


def calculate_client_fit(
    offered_budget: float,
    timeline_days: int,
    scope_clarity: int,
    communication: int,
    payment_reliability: int,
) -> dict:
    """
    Score client fit.

    Factors:
    - Budget adequacy
    - Timeline realism
    - Scope clarity
    - Communication quality
    - Payment reliability
    """
    # Budget component (0-30)
    budget_score = min(30, offered_budget / 100)

    # Timeline component (-15 to +15)
    timeline_score = max(-15, min(15, (timeline_days - 14) * 1.5))

    # Soft factors (0-55)
    soft_score = (scope_clarity * 10) + (communication * 8) + (payment_reliability * 8)

    # Total
    total = max(0, min(100, budget_score + timeline_score + soft_score))

    # Level
    if total >= 70:
        level = "good"
    elif total >= 45:
        level = "borderline"
    else:
        level = "poor"

    # Red flags
    red_flags = []
    if payment_reliability <= 2:
        red_flags.append("Payment reliability concerns")
    if scope_clarity <= 2:
        red_flags.append("Unclear project scope")
    if communication <= 2:
        red_flags.append("Poor communication patterns")
    if timeline_days < 7:
        red_flags.append("Unrealistic timeline")

    # Tips
    tips = [
        "Use milestone-based payments",
        "Clarify scope with acceptance criteria",
        "Set regular communication cadence",
        "Document all requirements in writing",
    ]

    return {
        "score": round(total, 2),
        "level": level,
        "red_flags": red_flags,
        "tips": tips,
    }


def calculate_scope_creep(
    extra_requests: int,
    hours_per_request: float,
    hourly_rate: float,
    delay_days: int,
) -> dict:
    """
    Calculate scope creep cost.

    Includes direct costs and delay impact.
    """
    # Direct additional cost
    direct = extra_requests * hours_per_request * hourly_rate

    # Delay cost (opportunity cost)
    delay_cost = delay_days * (hourly_rate * 2)  # 2x for opportunity cost

    # Total
    total = direct + delay_cost

    # Boundary message template
    boundary_message = (
        "Thanks for sharing these additional requirements. "
        "I've reviewed them and they represent a significant scope expansion. "
        "Here are your options:\n\n"
        f"1. **Change Order**: Add ${direct:,.0f} to the project budget\n"
        f"2. **Phase Split**: Move new items to Phase 2\n"
        f"3. **Timeline Extension**: Extend deadline by {delay_days} days\n\n"
        "Let me know which approach works best for you."
    )

    return {
        "direct_cost": round(direct, 2),
        "delay_cost": round(delay_cost, 2),
        "total_cost": round(total, 2),
        "boundary_message": boundary_message,
    }


def calculate_hourly_rate(
    target_income: float,
    billable_weeks: int,
    billable_hours: float,
    expenses: float,
    tax_rate: float,
) -> dict:
    """
    Calculate optimal hourly rate.

    Formula: (Target Income + Expenses) / (Billable Hours * (1 - Tax Rate))
    """
    # Annual billable hours
    annual_hours = billable_weeks * billable_hours

    # Required pre-tax income
    pre_tax_income = (target_income + expenses) / (1 - tax_rate / 100)

    # Hourly rate
    hourly_rate = pre_tax_income / annual_hours

    # Breakdown
    breakdown = {
        "target_net_income": target_income,
        "business_expenses": expenses,
        "tax_buffer": pre_tax_income * (tax_rate / 100),
        "total_required": pre_tax_income,
        "billable_hours": annual_hours,
    }

    # Market range (based on typical freelance rates)
    market_range = {
        "junior": max(hourly_rate * 0.6, 25),
        "mid": hourly_rate,
        "senior": min(hourly_rate * 1.8, 300),
    }

    return {
        "hourly_rate": round(hourly_rate, 2),
        "breakdown": breakdown,
        "market_range": {k: round(v, 2) for k, v in market_range.items()},
    }


def compare_freelance_vs_fulltime(
    freelance_rate: float,
    billable_hours: int,
    fulltime_salary: float,
    benefits_value: float,
    freelance_expenses: float,
) -> dict:
    """
    Compare freelance vs full-time effective earnings.
    """
    # Freelance effective
    freelance_gross = freelance_rate * billable_hours
    freelance_net = freelance_gross - freelance_expenses

    # Full-time effective
    fulltime_total = fulltime_salary + benefits_value

    # Difference
    difference = freelance_net - fulltime_total

    # Recommendation
    if difference > 10000:
        recommendation = "Freelancing appears more lucrative by ${:,.0f}".format(difference)
    elif difference < -10000:
        recommendation = "Full-time employment appears more lucrative by ${:,.0f}".format(abs(difference))
    else:
        recommendation = "Both options are financially similar. Consider non-financial factors."

    return {
        "freelance_effective": round(freelance_net, 2),
        "fulltime_effective": round(fulltime_total, 2),
        "difference": round(difference, 2),
        "recommendation": recommendation,
    }


# =============================================================================
# Agency Calculator Functions
# =============================================================================


def calculate_agency_profit(
    revenue: float,
    salaries: float,
    overhead: float,
    tax_rate: float,
) -> dict:
    """Calculate agency profit margin."""
    gross_profit = revenue - salaries
    operating_profit = gross_profit - overhead
    net_profit = operating_profit * (1 - tax_rate / 100)
    margin = (net_profit / revenue) * 100 if revenue > 0 else 0

    # Industry benchmark (typical agency margins: 10-20%)
    benchmark = 15.0

    return {
        "gross_profit": round(gross_profit, 2),
        "net_profit": round(net_profit, 2),
        "margin_percent": round(margin, 2),
        "benchmark": benchmark,
    }


def calculate_utilization(
    team_size: int,
    billable_count: int,
    available_hours: float,
    tracked_billable: float,
) -> dict:
    """Calculate team utilization rate."""
    total_available = team_size * available_hours
    utilization = (tracked_billable / total_available) * 100 if total_available > 0 else 0

    # Industry benchmark (typical: 70-80%)
    benchmark = 75.0

    # Lost revenue calculation
    target_billable = total_available * (benchmark / 100)
    lost_hours = target_billable - tracked_billable
    lost_revenue = max(0, lost_hours * 100)  # Assuming $100/hr average

    # Recommendations
    recommendations = []
    if utilization < 60:
        recommendations.append("Focus on lead generation to fill capacity")
    if billable_count < team_size * 0.8:
        recommendations.append("Convert more team members to billable roles")
    if utilization > 85:
        recommendations.append("Consider hiring to prevent burnout")

    return {
        "utilization_percent": round(utilization, 2),
        "benchmark": benchmark,
        "lost_revenue": round(lost_revenue, 2),
        "recommendations": recommendations,
    }


def calculate_client_ltv(
    avg_project_value: float,
    projects_per_year: int,
    retention_years: float,
    referral_value: float,
) -> dict:
    """Calculate client lifetime value."""
    annual_value = avg_project_value * projects_per_year
    lifetime_value = annual_value * retention_years
    total_referral = referral_value * retention_years

    return {
        "ltv": round(lifetime_value + total_referral, 2),
        "annual_value": round(annual_value, 2),
        "referral_value": round(total_referral, 2),
    }


def calculate_proposal_win_rate(
    sent: int,
    won: int,
    value_sent: float,
    value_won: float,
) -> dict:
    """Calculate proposal win rate."""
    win_rate = (won / sent) * 100 if sent > 0 else 0
    value_win_rate = (value_won / value_sent) * 100 if value_sent > 0 else 0

    # Industry benchmark (typical: 25-40%)
    benchmark = 33.0

    # Recommendations
    recommendations = []
    if win_rate < 20:
        recommendations.append("Review proposal qualification criteria")
    if win_rate > 50:
        recommendations.append("Consider bidding on more ambitious projects")
    if value_win_rate < win_rate:
        recommendations.append("Focus on higher-value proposals")

    return {
        "win_rate": round(win_rate, 2),
        "value_win_rate": round(value_win_rate, 2),
        "benchmark": benchmark,
        "recommendations": recommendations,
    }


def forecast_cash_flow(
    current_cash: float,
    receivables: float,
    payables: float,
    monthly_burn: float,
    expected_income: float,
) -> dict:
    """Forecast 90-day cash flow."""
    # Monthly forecast
    forecast = []
    running_cash = current_cash + receivables - payables

    for month in range(3):
        month_income = expected_income / 3  # Spread over 3 months
        ending_cash = running_cash + month_income - monthly_burn
        forecast.append({
            "month": month + 1,
            "starting": round(running_cash, 2),
            "income": round(month_income, 2),
            "expenses": round(monthly_burn, 2),
            "ending": round(ending_cash, 2),
        })
        running_cash = ending_cash

    # Runway calculation
    runway = running_cash / monthly_burn if monthly_burn > 0 else float('inf')

    # Risk level
    if runway < 3:
        risk = "high"
    elif runway < 6:
        risk = "medium"
    else:
        risk = "low"

    # Recommendations
    recommendations = []
    if risk == "high":
        recommendations.append("Prioritize collections on outstanding invoices")
        recommendations.append("Consider delaying non-essential expenses")
    elif risk == "medium":
        recommendations.append("Build 3-month cash reserve")

    return {
        "forecast": forecast,
        "runway": round(runway, 2),
        "risk_level": risk,
        "recommendations": recommendations,
    }


def calculate_break_even(
    fixed_costs: float,
    margin_percent: float,
) -> dict:
    """Calculate break-even point."""
    # Break-even revenue = Fixed Costs / Margin %
    margin_decimal = margin_percent / 100
    break_even_revenue = fixed_costs / margin_decimal if margin_decimal > 0 else float('inf')

    # Projects needed (assuming average project)
    avg_project = break_even_revenue * margin_decimal / 3  # Rough estimate
    projects_needed = break_even_revenue / avg_project if avg_project > 0 else 0

    # Daily target
    daily_target = break_even_revenue / 22  # Working days

    return {
        "monthly_revenue": round(break_even_revenue, 2),
        "projects_needed": round(projects_needed, 1),
        "daily_revenue": round(daily_target, 2),
    }


# =============================================================================
# Shared Calculator Functions
# =============================================================================


# PPP multipliers by country tier
PPP_MULTIPLIERS = {
    # Tier 0 (1.0x) - US, UK, CA, AU, DE, FR, JP
    "US": 1.0, "GB": 1.0, "CA": 1.0, "AU": 1.0, "DE": 1.0, "FR": 1.0, "JP": 1.0,
    # Tier 1 (0.7x) - IT, ES, PT, GR, KR, TW
    "IT": 0.7, "ES": 0.7, "PT": 0.7, "GR": 0.7, "KR": 0.7, "TW": 0.7,
    # Tier 2 (0.5x) - PL, CZ, BR, MX, AR, CL
    "PL": 0.5, "CZ": 0.5, "BR": 0.5, "MX": 0.5, "AR": 0.5, "CL": 0.5,
    # Tier 3 (0.3x) - IN, PH, VN, ID, PK, NG
    "IN": 0.3, "PH": 0.3, "VN": 0.3, "ID": 0.3, "PK": 0.3, "NG": 0.3,
    # Tier 4 (0.2x) - UA, EG, MA, NP, LK
    "UA": 0.2, "EG": 0.2, "MA": 0.2, "NP": 0.2, "LK": 0.2,
}


def calculate_ppp_adjusted_rate(
    base_rate: float,
    base_country: str,
    target_country: str,
    user_type: str,
) -> dict:
    """Calculate PPP-adjusted rate."""
    base_multiplier = PPP_MULTIPLIERS.get(base_country.upper(), 1.0)
    target_multiplier = PPP_MULTIPLIERS.get(target_country.upper(), 1.0)

    # PPP adjustment
    ppp_multiplier = target_multiplier / base_multiplier if base_multiplier > 0 else 1.0
    adjusted_rate = base_rate * ppp_multiplier

    # Local market rate (typical range)
    local_market = {
        "low": adjusted_rate * 0.7,
        "high": adjusted_rate * 1.3,
    }

    # Recommendation
    if user_type == "individual":
        recommendation = f"Consider charging ${adjusted_rate:.0f}/hr for {target_country} clients"
    else:
        recommendation = f"Adjust agency rates to ${adjusted_rate:.0f}/hr for {target_country} market"

    return {
        "adjusted_rate": round(adjusted_rate, 2),
        "ppp_multiplier": round(ppp_multiplier, 3),
        "local_market_rate": local_market,
        "recommendation": recommendation,
    }


def estimate_taxes(
    annual_income: float,
    expenses: float,
    country: str,
    user_type: str,
) -> dict:
    """Estimate quarterly taxes (simplified)."""
    taxable_income = annual_income - expenses

    # Simplified tax rates by country
    tax_rates = {
        "US": 0.25,  # Self-employment + income tax estimate
        "GB": 0.27,
        "CA": 0.23,
        "AU": 0.29,
        "DE": 0.30,
    }

    rate = tax_rates.get(country.upper(), 0.25)
    estimated_tax = taxable_income * rate
    effective_rate = (estimated_tax / annual_income) * 100 if annual_income > 0 else 0
    quarterly = estimated_tax / 4

    # Common deductions
    deductions = [
        "Home office expense",
        "Equipment and software",
        "Professional development",
        "Health insurance premiums",
        "Retirement contributions",
    ]

    return {
        "estimated_tax": round(estimated_tax, 2),
        "effective_rate": round(effective_rate, 2),
        "quarterly_payment": round(quarterly, 2),
        "common_deductions": deductions,
    }


def plan_retirement(
    current_age: int,
    retirement_age: int,
    current_savings: float,
    annual_income: float,
    replacement_rate: float,
) -> dict:
    """Plan retirement savings."""
    years_to_retire = retirement_age - current_age
    annual_needed = annual_income * replacement_rate

    # Assume 7% annual return, 3% inflation (net 4%)
    net_return = 0.04

    # Future value of current savings
    future_current = current_savings * ((1 + net_return) ** years_to_retire)

    # Total needed (25x annual for 4% withdrawal rate)
    total_needed = annual_needed * 25

    # Shortfall
    shortfall = total_needed - future_current

    # Monthly contribution needed
    if years_to_retire > 0 and shortfall > 0:
        monthly = shortfall / years_to_retire / 12
    else:
        monthly = 0

    return {
        "monthly_contribution": round(max(0, monthly), 2),
        "annual_contribution": round(max(0, monthly * 12), 2),
        "projected_total": round(future_current, 2),
        "shortfall": round(max(0, shortfall), 2),
    }


def calculate_time_value(
    hourly_rate: float,
    task_hours: float,
    outsourcing_cost: float,
    user_type: str,
) -> dict:
    """Calculate time value and outsourcing ROI."""
    opportunity_cost = hourly_rate * task_hours
    roi = ((opportunity_cost - outsourcing_cost) / outsourcing_cost) * 100 if outsourcing_cost > 0 else 0

    # Recommendation
    if roi > 100:
        recommendation = "Strong case for outsourcing - focus on high-value work"
    elif roi > 0:
        recommendation = "Consider outsourcing if quality is reliable"
    else:
        recommendation = "May be better to handle in-house"

    return {
        "opportunity_cost": round(opportunity_cost, 2),
        "recommendation": recommendation,
        "roi": round(roi, 2),
    }
