# Practical scenario tools

These tools calculate with explicit assumptions. They are not country-specific
tax advice, observed market-rate data or guaranteed investment outcomes.

## Cost-of-living scenario

POST /calculators/cost-of-living

```json
{"base_rate":100,"cost_ratio":0.6,"currency":"USD","base_country":"US","target_country":"KE"}
```

Result: 60 USD per hour in the scenario. Formula: base rate times cost ratio.
Compare costs in the same currency and period to construct your ratio. Country
labels do not trigger a dataset lookup. No exchange conversion occurs.
Legacy /rate-ppp remains an alias; ppp_multiplier is the supplied ratio, not
verified PPP. local_market_rate stays null because we do not have that evidence.
This is not a recommendation to discount work based on a freelancer's nationality.

## Tax reserve

POST /calculators/tax-reserve

```json
{"annual_income":50000,"business_expenses":10000,"reserve_rate_percent":25,"currency":"USD","country":"US"}
```

Result: annual reserve 10000; equal-quarter allocation 2500. The selected
percentage applies to max(0, income - entered expenses). No negative refund is
inferred. An expense is not automatically a legally deductible expense.
Country is informational; no brackets, credits, filing status, social insurance,
deadlines or jurisdictional rules are inferred. Choose a percentage using your
own local advice. /tax-estimator remains an alias; estimated_tax and
quarterly_payment are compatibility names for budget allocations, not tax owed.

## Retirement funding scenario

POST /calculators/retirement

```json
{"current_age":40,"retirement_age":60,"current_retirement_savings":10000,"annual_income":30000,"desired_replacement_rate":0.8,"annual_return_percent":6,"inflation_percent":2,"withdrawal_rate_percent":4,"currency":"USD"}
```

All amounts are in today's money. Effective real annual return =
(1 + nominal return)/(1 + inflation) - 1. Convert to an effective monthly return.
Target = income times replacement fraction divided by withdrawal fraction.
Existing savings compound for the selected horizon. Solve the end-of-month
annuity for the remaining target; round required monthly contributions upward
to the nearest cent. Contributions must rise with inflation to maintain this
real amount. At zero real return, divide shortfall by the number of months.

projected_total includes the calculated contributions;
projected_without_contributions does not. shortfall is before new contributions.
Withdrawal rate is the user's scenario, not a guaranteed sustainable policy.
Taxes, fees, pensions, longevity and sequence-of-returns risk are not modeled.
Test lower returns and higher inflation as separate scenarios.

## Restored business and learning utility

- Break-even: optional average_project_value gives a rounded-up whole project
  count. Without it, project count is unknown rather than invented.
- Utilization: target_utilization_percent defaults visibly to an editable 75%.
  average_hourly_rate enables a hypothetical capacity revenue gap, not booked
  revenue. Legacy benchmark means the selected target, not an industry statistic.
- Skill gaps: target_skills overrides the starter role template. A copywriter,
  designer or any other user can supply real project requirements. Current skills
  are compared against these targets. Unsupported roles get a concrete manual
  workflow rather than an invented developer curriculum.
- Learning references: a small checked catalog of Python, MDN and PostgreSQL
  starting resources. Missing catalog coverage remains explicit; no generated URLs.

## Compatibility and limits

Clients must provide currency and new financial assumptions; old payloads return
422 with missing-field details rather than silently assuming rates. The currency
field validates three uppercase letters, not membership in a live ISO registry.
Financial scenario inputs are bounded and non-finite numbers rejected. This is
planning arithmetic, not accounting-grade ledger rounding.
Current tests cover HTTP contracts, negative/zero real returns, funded targets,
invalid ages, invalid rates, losses and independent month-by-month projections.

## Sources and scope

- [Investor.gov compound interest calculator](https://www.investor.gov/financial-tools-calculators/calculators/compound-interest-calculator):
  precedent for user-selected contribution/return scenarios, not validation of our retirement assumptions.
- [IRS estimated taxes](https://www.irs.gov/businesses/small-businesses-self-employed/estimated-taxes):
  actual liability requires more information than our reserve model.
- [World Bank ICP FAQ](https://www.worldbank.org/en/programs/icp/faq):
  PPP is not an exchange quote or a freelance market-rate table.
- [Python tutorial](https://docs.python.org/3/tutorial/),
  [MDN learning](https://developer.mozilla.org/en-US/docs/Learn_web_development),
  [PostgreSQL tutorial](https://www.postgresql.org/docs/current/tutorial.html).

References checked 2026-09-19. No runtime network lookup is required.
