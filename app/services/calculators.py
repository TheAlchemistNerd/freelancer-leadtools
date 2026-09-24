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
    target_skills: list[str] | None = None,
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
    target_lower = target_role.lower().replace(" ", "").replace("-", "")
    matched_skills = []
    for role, skills in templates.items():
        if role in target_lower:
            matched_skills = skills
            break

    if target_skills:
        matched_skills = list(dict.fromkeys(s.lower().strip() for s in target_skills if s.strip()))

    if not matched_skills:
        return {
            "normalized_skills": [s.lower().strip() for s in current_skills],
            "gaps": [],
            "roadmap": ["List 1-3 capabilities required by a real project in target_skills.",
                        "Choose a small deliverable that demonstrates one capability.",
                        "Record feedback and evidence in DevLog, then reassess the remaining gaps."],
            "resources": [],
        }

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
    # Small editorial catalog, checked 2026-09-19. These are starting references,
    # not a claim that every missing skill has a complete learning curriculum.
    catalog = {
        "python": "https://docs.python.org/3/tutorial/",
        "javascript": "https://developer.mozilla.org/en-US/docs/Learn_web_development",
        "css": "https://developer.mozilla.org/en-US/docs/Learn_web_development",
        "sql": "https://www.postgresql.org/docs/current/tutorial.html",
    }
    resources = list(dict.fromkeys(catalog[gap] for gap in gaps if gap in catalog))

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
    displaced_billable_hours: float = 0,
    currency: str = "USD",
) -> dict:
    """
    Calculate scope creep cost.

    Includes direct costs and delay impact.
    """
    # Direct additional cost
    direct = extra_requests * hours_per_request * hourly_rate

    # Delay cost (opportunity cost)
    delay_cost = displaced_billable_hours * hourly_rate

    # Total
    total = direct + delay_cost

    # Boundary message template
    boundary_message = (
        "Thanks for sharing these additional requirements. "
        "I've reviewed them and they represent a significant scope expansion. "
        "Here are your options:\n\n"
        f"1. **Change Order**: Add {currency} {direct:,.2f} to the project budget\n"
        f"2. **Phase Split**: Move new items to Phase 2\n"
        f"3. **Timeline Extension**: Extend deadline by {delay_days} days\n\n"
        "Let me know which approach works best for you."
    )

    return {
        "direct_cost": round(direct, 2),
        "delay_cost": round(delay_cost, 2),
        "total_cost": round(total, 2),
        "boundary_message": boundary_message,
        "currency": currency,
        "assumptions": ["Delay days do not automatically imply lost revenue.",
                        "Opportunity cost uses only supplied displaced billable hours; avoid double counting.",
                        "Only direct additional work is included in the proposed change-order amount."],
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
    market_range = {}  # This is a personal rate floor, not market research.

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
    net_profit = operating_profit - max(0, operating_profit) * tax_rate / 100
    margin = (net_profit / revenue) * 100 if revenue > 0 else 0

    # Industry benchmark (typical agency margins: 10-20%)
    benchmark = None  # No verified industry dataset.

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
    target_percent: float = 75,
    hourly_rate: float | None = None,
) -> dict:
    """Calculate team utilization rate."""
    total_available = team_size * available_hours
    utilization = (tracked_billable / total_available) * 100 if total_available > 0 else 0

    # Industry benchmark (typical: 70-80%)
    benchmark = target_percent  # User-editable scenario, not an industry statistic.

    # Lost revenue calculation
    target_billable = total_available * (benchmark / 100)
    lost_hours = target_billable - tracked_billable
    lost_revenue = round(max(0, lost_hours) * hourly_rate, 2) if hourly_rate is not None else None

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
        "lost_revenue": lost_revenue,
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
    benchmark = None  # No verified industry dataset.

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
    average_project_value: float | None = None,
) -> dict:
    """Calculate break-even point."""
    # Break-even revenue = Fixed Costs / Margin %
    margin_decimal = margin_percent / 100
    break_even_revenue = fixed_costs / margin_decimal if margin_decimal > 0 else float('inf')

    # Projects needed (assuming average project)
    from math import ceil
    projects_needed = ceil(break_even_revenue / average_project_value) if average_project_value else None

    # Daily target
    daily_target = break_even_revenue / 22  # Working days

    return {
        "monthly_revenue": round(break_even_revenue, 2),
        "projects_needed": projects_needed,
        "daily_revenue": round(daily_target, 2),
    }


# =============================================================================
# Shared Calculator Functions
# =============================================================================


# Cost, tax-reserve and retirement scenarios live in scenarios.py.


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
