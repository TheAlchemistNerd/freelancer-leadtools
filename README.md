# Freelancer LeadTools

**Free Marketing Calculators for Lead Generation and Customer Acquisition**

**Author:** Nevil Maloba

---

## Purpose and Strategic Role

Freelancer LeadTools provides public calculators and a consent-aware workspace for freelancers and agencies. It is intended to introduce users to the wider OSFreelance product; acquisition and conversion performance are not yet established.

The strategic objectives encompass attracting potential users through valuable free tools, educating users about their freelance business health across multiple dimensions, and converting users to paid products through targeted calls-to-action positioned strategically within calculator results.

---

## Calculator Categories and Capabilities

### Individual Freelancer Calculators

These calculators target individual freelancers and funnel users toward Freelance Growth subscriptions.

| Calculator | Description | Call-to-Action |
|------------|-------------|----------------|
| Burnout Risk Calculator | Assess burnout risk based on work habits, sleep patterns, and context switching frequency | Get personalized coaching |
| Skill Gap Scanner | Identify skills needed for your target role or income level | Create learning plan |
| Portfolio Score | Evaluate portfolio strength with actionable improvement recommendations | Get improvement plan |
| Client Fit Score | Evaluate if a client is worth working with based on multiple factors | Track client relationships |
| Scope Creep Calculator | Calculate cost of additional requests and change orders | Set boundaries with templates |
| Hourly Rate Calculator | Determine optimal hourly rate based on financial requirements | Get accurate time tracking |
| Freelance vs Full-time ROI | Compare earnings potential between freelance and employment | Manage freelance finances |

### Agency Calculators

These calculators target agency owners and funnel users toward Freelancer DealFlow subscriptions.

| Calculator | Description | Call-to-Action |
|------------|-------------|----------------|
| Agency Profit Margin | Calculate actual profit after all expenses and overhead | Track agency finances |
| Team Utilization Rate | Measure team productivity and capacity utilization | Optimize team capacity |
| Client Lifetime Value | Calculate client lifetime value for strategic decisions | Manage client relationships |
| Proposal Win Rate | Analyze proposal success rates and patterns | Improve proposals with AI |
| Cash Flow Forecast | Predict future cash position based on pipeline | Manage agency finances |
| Break-even Analysis | Determine minimum revenue needed for profitability | Track agency metrics |

### Shared Calculators

These calculators serve both individual freelancers and agencies, funneling users toward either product based on their profile.

| Calculator | Description | Call-to-Action |
|------------|-------------|----------------|
| Rate Calculator with PPP | Location-adjusted rate calculator using PPP data | Get accurate time tracking |
| Tax Estimator | Estimate quarterly taxes based on income and expenses | Track business expenses |
| Retirement Planner | Plan for retirement as a freelancer or agency owner | Plan long-term finances |
| Time Value Calculator | Calculate opportunity cost of activities | Optimize time allocation |

---

## Technical Architecture

```
freelancer-leadtools/
├── app/                    # FastAPI backend application
│   ├── main.py             # Application entry point
│   ├── routes/
│   │   ├── individuals.py  # Individual freelancer calculator APIs
│   │   ├── agencies.py     # Agency calculator APIs
│   │   ├── shared.py       # Shared calculator APIs
│   │   ├── web.py          # Server-rendered homepage, tools and methodology
│   │   └── workspace.py    # Same-origin account and product handoff workspace
│   ├── schemas/            # Pydantic request/response validation
│   ├── services/           # Deterministic formulas and reference data
│   ├── repositories/       # PostgreSQL lead and reference-data persistence
│   └── static/             # Branded CSS, JavaScript and image assets
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
└── vercel.json             # Vercel deployment configuration
```

---

## Lead Capture Strategy

The lead capture funnel operates through a structured progression from free value delivery to email capture to paid product conversion.

Users begin at free calculators where they input data such as weekly hours, sleep patterns, and context switches. Upon calculation, users receive basic interpretations and immediate tips without any barrier. The results page then presents an option to receive comprehensive analysis via email, requiring email address submission. This represents the lead capture point. Finally, users encounter calls-to-action for paid products offering ongoing tracking and coaching capabilities.

---

## Technology Stack

| Component | Technology Selection |
|-----------|---------------------|
| Backend Framework | FastAPI |
| Public interface | FastAPI JSON API plus server-rendered branded tools and workspace |
| Durable storage | PostgreSQL via SQLAlchemy and Alembic |
| Ephemeral coordination | Redis rate limits, deduplication, and CRM event stream |
| Deployment | LeadTools API/container serves both API and same-origin browser UI |
| Separate frontend | Not part of this release; reconsider only with measured need |

---

## SEO Strategy

Each calculator targets specific search keywords to maximize organic traffic acquisition:

| Calculator | Target Keywords |
|------------|-----------------|
| Burnout Calculator | freelance burnout test, burnout risk calculator |
| Rate Calculator | freelance hourly rate calculator, what should I charge |
| Portfolio Score | portfolio review for freelancers, portfolio strength |
| Agency Profit | agency profit margin calculator, creative agency profits |

---

## Design Principles

**Performance:** Page load times must remain under 2 seconds across all calculators.

**Mobile-First Design:** Over 60 percent of traffic originates from mobile devices, requiring responsive design prioritization.

**Accessibility:** WCAG 2.1 AA compliance ensures accessibility for all users.

**Shareability:** Results should be easily shareable on social media platforms to amplify organic reach.

---

## Security Architecture

LeadTools implements comprehensive security measures despite being a public API without authentication requirements.

**Rate Limiting:** Redis-backed sliding window algorithm limits requests to 100 per minute per IP address, with lower limits for lead capture endpoints to prevent spam.

**XSS Protection:** Pattern-based input sanitization blocks script tags, JavaScript protocols, event handlers, iframes, and other dangerous patterns.

**CSRF Protection:** Origin and Referer header validation on state-changing requests, with optional token-based protection for form submissions.

**Security Headers:** All responses include X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, and Content-Security-Policy headers.

**Request Size Limits:** Maximum body size of 1 MB and URL length of 2 KB prevent denial of service through large payloads.

**Bot Protection:** User-Agent analysis blocks known bad bots while allowing search engine crawlers.

For comprehensive security architecture details, reference the SECURITY_ARCHITECTURE.md document within the docs directory.

---

## Redis Storage Architecture

LeadTools uses PostgreSQL as the durable source of truth for captured leads and consent state. Redis is an optional acceleration and coordination layer; an outage must not discard a lead or an unsubscribe request.

**Lead Storage:** Leads and their consent state are committed to PostgreSQL. Redis performs atomic duplicate suppression and emits CRM synchronization events when available.

**Public calculators:** Calculator requests are stateless. No server-side calculator session is required.

**Analytics:** Product analytics is not yet implemented and must not be inferred from the Redis integration.

For detailed Redis architecture including key patterns and data structures, reference the SECURITY_ARCHITECTURE.md document.

---

## License

MIT License - see LICENSE file for complete terms.

---

**Part of the Freelancer Ecosystem**

- [freelancer-core](https://github.com/your-org/freelancer-core) - Shared infrastructure library
- [freelance-growth](https://github.com/your-org/freelance-growth) - Individual freelancer SaaS
- [freelancer-dealflow](https://github.com/your-org/freelancer-dealflow) - Agency management SaaS

*Author: Nevil Maloba*  
*Last Updated: September 2026*
> Current implementation note: route contracts are regression-tested. Cost-of-living,
> tax-reserve and retirement tools now use explicit user assumptions, not invented
> country rates. Legacy URLs remain aliases but require the new scenario inputs.
> Unknown market/benchmark metrics are empty or null, not verified estimates.
> The public UI and workspace are implemented in the LeadTools service. The
> workspace proxies authenticated product handoffs; real cross-service
> PostgreSQL/Redis journeys still need a fresh run for this release.
> See the root docs/internal/leadtools-execution-plan.md for current work.

### Scenario tools (current API)

See [scenario methodology and examples](docs/SCENARIO_TOOLS.md). These tools do
not require an AI provider, external data subscription, or login.
