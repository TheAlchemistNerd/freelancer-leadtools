"""Exercise public calculator request/response contracts, without external I/O."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes import individuals, agencies, shared

app = FastAPI()
for router in (individuals.router, agencies.router, shared.router):
    app.include_router(router, prefix="/calculators")
client = TestClient(app)

CASES = {
    "burnout": {"weekly_hours": 35, "context_switches_per_day": 5, "avg_sleep_hours": 8},
    "skill-gap": {"target_role": "backend", "current_skills": ["python"], "experience_level": "junior"},
    "portfolio": {"project_links": []},
    "client-fit": {"offered_budget": 5000, "proposed_timeline_days": 30, "scope_clarity_score": 4, "communication_quality_score": 4, "payment_reliability_signal": 4},
    "scope-creep": {"extra_requests_count": 2, "avg_hours_per_request": 3, "hourly_rate": 50, "delivery_delay_days": 2},
    "hourly-rate": {"target_annual_income": 60000},
    "freelance-vs-fulltime": {"freelance_hourly_rate": 60, "expected_billable_hours": 1000, "fulltime_annual_salary": 50000},
    "agency-profit": {"annual_revenue": 100000, "total_salaries": 50000, "annual_overhead": 10000, "effective_tax_rate": 20},
    "utilization": {"total_team_size": 2, "billable_team_members": 2, "available_hours_per_week": 40, "tracked_billable_hours": 50},
    "client-ltv": {"average_project_value": 1000, "projects_per_year": 3, "average_retention_years": 2},
    "proposal-win-rate": {"proposals_sent": 10, "proposals_won": 3, "total_value_sent": 10000, "total_value_won": 3000},
    "cash-flow": {"current_cash": 10000, "accounts_receivable": 500, "accounts_payable": 100, "monthly_operating_expenses": 1000, "expected_new_revenue": 3000},
    "break-even": {"monthly_fixed_costs": 1000, "average_project_margin_percent": 50},
    "rate-ppp": {"base_rate": 100, "base_country": "US", "target_country": "KE", "cost_ratio": 0.6, "currency": "USD"},
    "tax-estimator": {"annual_income": 50000, "country": "US", "reserve_rate_percent": 25, "currency": "USD"},
    "retirement": {"current_age": 30, "retirement_age": 65, "current_retirement_savings": 1000, "annual_income": 60000, "annual_return_percent": 5, "inflation_percent": 2, "withdrawal_rate_percent": 4, "currency": "USD"},
    "time-value": {"hourly_rate": 50, "task_hours": 10, "outsourcing_cost": 100},
}
WITHDRAWN = set()

def test_inconsistent_wins_rejected():
    payload = dict(CASES["proposal-win-rate"], proposals_won=11)
    assert client.post("/calculators/proposal-win-rate", json=payload).status_code == 422

def test_nonfinite_input_rejected():
    payload = dict(CASES["hourly-rate"], target_annual_income="Infinity")
    assert client.post("/calculators/hourly-rate", json=payload).status_code == 422

@pytest.mark.parametrize("slug", CASES)
def test_valid_contract(slug):
    response = client.post("/calculators/" + slug, json=CASES[slug])
    assert response.status_code == (503 if slug in WITHDRAWN else 200), response.text
    if slug not in WITHDRAWN:
        assert response.json()["cta"]["url"].startswith("https://")

@pytest.mark.parametrize("slug", [s for s in CASES if s != "portfolio"])
def test_missing_fields_rejected(slug):
    assert client.post("/calculators/" + slug, json={}).status_code == 422

def test_unsupported_role_does_not_invent_developer_gaps():
    payload = dict(CASES["skill-gap"], target_role="copywriter")
    body = client.post("/calculators/skill-gap", json=payload).json()
    assert body["gaps"] == []
    assert body["resources"] == []

def test_unknown_business_metrics_are_not_fabricated():
    assert client.post("/calculators/hourly-rate", json=CASES["hourly-rate"]).json()["market_range"] == {}
    assert client.post("/calculators/break-even", json=CASES["break-even"]).json()["projects_needed"] is None
    assert client.post("/calculators/utilization", json=CASES["utilization"]).json()["lost_revenue"] is None

@pytest.mark.parametrize("slug", ["hourly-rate", "client-fit", "scope-creep", "freelance-vs-fulltime"])
def test_commercial_cta_targets_dealflow(slug):
    assert "dealflow" in client.post("/calculators/" + slug, json=CASES[slug]).json()["cta"]["url"]
