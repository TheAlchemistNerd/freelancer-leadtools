"""Explicit-assumption planning arithmetic; no inferred market or statutory rates."""
import math


def cost_scenario(rate, ratio):
    return round(rate * ratio, 2)


def tax_reserve(income, expenses, rate):
    profit = max(0, income - expenses)
    reserve = round(profit * rate / 100, 2)
    return reserve, round(reserve / 4, 2), round(reserve / income * 100, 2)


def retirement_scenario(current_age, retirement_age, savings, income,
                        replacement, annual_return, inflation, withdrawal):
    """Today's-money annuity; end-of-month contributions rise with inflation."""
    months = (retirement_age - current_age) * 12
    real_annual = (1 + annual_return / 100) / (1 + inflation / 100) - 1
    log_monthly = math.log1p(real_annual) / 12
    growth = math.exp(log_monthly * months)
    monthly_rate = math.expm1(log_monthly)
    annuity = months if abs(monthly_rate) < 1e-12 else math.expm1(log_monthly * months) / monthly_rate
    target = income * replacement / (withdrawal / 100)
    existing = savings * growth
    shortfall = max(0, target - existing)
    monthly = math.ceil(shortfall / annuity * 100) / 100
    return {
        "monthly_contribution": monthly,
        "annual_contribution": round(monthly * 12, 2),
        "projected_total": round(existing + monthly * annuity, 2),
        "projected_without_contributions": round(existing, 2),
        "target_total": round(target, 2),
        "shortfall": round(shortfall, 2),
    }
