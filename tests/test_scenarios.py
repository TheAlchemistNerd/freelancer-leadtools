import pytest
from app.services.scenarios import retirement_scenario, tax_reserve
from tests.test_calculator_http import client, CASES


def test_zero_real_return():
    result = retirement_scenario(40, 50, 0, 12000, 1, 3, 3, 10)
    assert result["target_total"] == 120000
    assert result["monthly_contribution"] == 1000
    assert result["projected_total"] == 120000


@pytest.mark.parametrize("annual_return,inflation", [(6, 2), (-5, 3), (0, 0)])
def test_projection_matches_month_by_month(annual_return, inflation):
    result = retirement_scenario(40, 60, 10000, 30000, .8, annual_return, inflation, 4)
    monthly_rate = ((1 + annual_return / 100) / (1 + inflation / 100)) ** (1 / 12) - 1
    balance = 10000
    for _ in range(240):
        balance = balance * (1 + monthly_rate) + result["monthly_contribution"]
    assert result["projected_total"] == pytest.approx(balance, abs=.01)
    assert balance >= result["target_total"] - .01


def test_funded_target_requires_no_more_contributions():
    assert retirement_scenario(40, 50, 1000000, 10000, .8, 0, 0, 4)["monthly_contribution"] == 0


def test_loss_does_not_create_tax_refund():
    assert tax_reserve(10000, 20000, 25) == (0, 0, 0)
    assert tax_reserve(10000, 2000, 25) == (2000, 500, 20)


@pytest.mark.parametrize("slug,field,value", [
    ("rate-ppp", "cost_ratio", 0), ("tax-estimator", "reserve_rate_percent", 101),
    ("retirement", "retirement_age", 30), ("retirement", "withdrawal_rate_percent", 0),
    ("retirement", "annual_return_percent", "Infinity"),
])
def test_invalid_scenarios(slug, field, value):
    assert client.post("/calculators/" + slug, json=dict(CASES[slug], **{field: value})).status_code == 422


def test_cost_ratio_not_country_guess():
    body = client.post("/calculators/rate-ppp", json=CASES["rate-ppp"]).json()
    assert body["adjusted_rate"] == 60
    assert body["local_market_rate"] is None
    assert body["formula_version"] == "cost-ratio-v1"


def test_real_project_value_makes_project_count_useful():
    body = client.post("/calculators/break-even", json=dict(CASES["break-even"], average_project_value=750)).json()
    assert body["projects_needed"] == 3


def test_explicit_capacity_rate():
    body = client.post("/calculators/utilization", json=dict(
        CASES["utilization"], target_utilization_percent=75, average_hourly_rate=50)).json()
    assert body["lost_revenue"] == 500


def test_custom_learning_targets_support_non_developers():
    body = client.post("/calculators/skill-gap", json=dict(
        CASES["skill-gap"], target_role="copywriter", current_skills=["research"],
        target_skills=["research", "editing", "editing"])).json()
    assert body["gaps"] == ["editing"]


@pytest.mark.parametrize("new,old", [("cost-of-living", "rate-ppp"), ("tax-reserve", "tax-estimator")])
def test_clear_names_and_legacy_aliases_match(new, old):
    assert client.post("/calculators/" + new, json=CASES[old]).json() == client.post("/calculators/" + old, json=CASES[old]).json()


def test_learning_references_are_curated():
    body = client.post("/calculators/skill-gap", json=dict(
        CASES["skill-gap"], current_skills=[], target_skills=["python", "sql"])).json()
    assert body["resources"] == [
        "https://docs.python.org/3/tutorial/",
        "https://www.postgresql.org/docs/current/tutorial.html"]
