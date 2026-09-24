"""Server-rendered public pages, enhanced by a small same-origin API client."""

from html import escape

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.config import settings
from app.routes.estimates import EstimateRequest
from app.schemas import (
    CashFlowRequest,
    ClientFitRequest,
    HourlyRateRequest,
    ScopeCreepRequest,
    SkillGapRequest,
)

router = APIRouter()
TOOLS = {
    "hourly-rate": (
        "Find your rate floor",
        "Plan the rate needed for your annual income goal.",
        HourlyRateRequest,
        "A personal planning floor, not an observed market price. Annual income and "
        "expenses must use the same currency. Tax percentage is an assumed reserve.",
    ),
    "project-estimate": (
        "Price a project",
        "Turn effort, costs and contingency into an estimate.",
        EstimateRequest,
        "Hours × hourly rate + expenses, with your contingency applied. Excludes taxes and fees.",
    ),
    "scope-creep": (
        "Price extra work",
        "See the cost of requests beyond the original scope.",
        ScopeCreepRequest,
        "Direct cost = requests × hours per request × rate. Opportunity cost uses "
        "explicitly displaced paid hours, never delay days alone. Avoid double counting. "
        "Opportunity cost is not automatically money owed.",
    ),
    "client-fit": (
        "Qualify a client",
        "Make budget, scope and communication explicit.",
        ClientFitRequest,
        "A heuristic based on your answers, not a prediction of client behavior or creditworthiness.",
    ),
    "cash-flow": (
        "Explore your cash runway",
        "Model a simple three-month cash scenario.",
        CashFlowRequest,
        "Receivables and payables settle immediately; expected revenue is spread "
        "across three months. This simplified scenario does not model actual payment dates.",
    ),
    "skill-gap": (
        "Plan your next capability",
        "Compare a project's target skills with what you already know.",
        SkillGapRequest,
        "Enter comma-separated skills. Custom target skills override developer starter "
        "templates. Results are a checklist, not proof of competence.",
    ),
}


def page(title: str, body: str) -> HTMLResponse:
    page_title = f"{title} · OSFreelance"
    description = "Practical free tools for independent work. Transparent assumptions. No signup needed."
    image_url = (
        f"{settings.web_public_origin.rstrip('/')}/tool-assets/brand/social-card.png"
    )
    workspace_nav = (
        '<a href="/workspace">Workspace</a>'
        if settings.identity_api_url and settings.workspace_dealflow_url else ""
    )
    return HTMLResponse(
        f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(page_title)}</title>
<meta name="description" content="{escape(description, quote=True)}">
<meta name="theme-color" content="#F6F4EF">
<meta property="og:type" content="website"><meta property="og:site_name" content="OSFreelance">
<meta property="og:title" content="{escape(page_title, quote=True)}">
<meta property="og:description" content="{escape(description, quote=True)}">
<meta property="og:image" content="{escape(image_url, quote=True)}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="OSFreelance — Make independent work work.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(page_title, quote=True)}">
<meta name="twitter:description" content="{escape(description, quote=True)}">
<meta name="twitter:image" content="{escape(image_url, quote=True)}">
<link rel="icon" href="/tool-assets/brand/favicon.svg" type="image/svg+xml">
<link rel="alternate icon" href="/tool-assets/brand/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/tool-assets/brand/apple-touch-icon.png">
<link rel="manifest" href="/tool-assets/brand/site.webmanifest">
<link rel="stylesheet" href="/tool-assets/tools.css">
<script defer src="/tool-assets/tools.js"></script>
</head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="/tools">OS<span>Freelance</span></a>
<nav aria-label="Main"><a href="/tools">Free tools</a>
<a href="/methodology">How data works</a>{workspace_nav}<a href="/docs">API</a></nav></header>
<main id="main">{body}</main><footer>Independent work. Clear decisions.<br>
Calculations are planning aids. Inputs are sent to this service to calculate results;
no email is required. This preview has no analytics or advertising scripts.
</footer></body></html>"""
    )


@router.get("/tools", response_class=HTMLResponse)
def index():
    cards = "".join(
        f'<a class="card" href="/tools/{slug}"><span>FREE TOOL</span>'
        f"<h2>{escape(item[0])}</h2><p>{escape(item[1])}</p><b>Open tool →</b></a>"
        for slug, item in TOOLS.items()
    )
    trust = """<section class="trust" aria-labelledby="data-trust-heading">
<p class="eyebrow">DATA YOU CAN QUESTION</p>
<h2 id="data-trust-heading">Real context, not invented benchmarks.</h2>
<p>Today, every free tool uses the assumptions you enter and a named formula version.
As connected features are released, OSFreelance will add only owner-authorized work
history and cited public reference data.</p>
<div class="status-grid">
<article><h3>Your inputs</h3><p>Explicit assumptions for one calculation. They remain
visibly separate from observed facts.</p></article>
<article><h3>Your work history</h3><p>Planned connections to DealFlow and TimeBank
will use your confirmed invoices, hours and project outcomes—not another freelancer's
private records.</p></article>
<article><h3>Public context</h3><p>When available, every observation will show its
source, place, period, freshness and limitations.</p></article>
</div>
<p><a class="text-link" href="/methodology">See how our data works →</a></p>
</section>"""
    return page(
        "Make independent work work",
        '<section class="hero"><p class="eyebrow">YOUR INDEPENDENT WORKBENCH</p>'
        "<h1>Make independent<br>work work.</h1><p>Price your projects. Protect your "
        'time.<br>Build your next skill.</p><a class="button" href="#tools">Find your '
        'next tool ↓</a></section><section id="tools"><h2>What are you working on?</h2>'
        f'<div class="grid">{cards}</div></section>{trust}',
    )


@router.get("/methodology", response_class=HTMLResponse)
def methodology():
    return page(
        "How our data works",
        """<article class="methodology">
<p class="eyebrow">OUR DATA PROMISE</p>
<h1>Useful numbers should be explainable.</h1>
<p class="lede">LeadTools combines explicit user assumptions, owner-authorized
operating history and carefully limited public reference data. It does not invent
an industry average when evidence is missing.</p>

<section aria-labelledby="flow-heading"><h2 id="flow-heading">The safe data path</h2>
<ol class="data-flow"><li>Scheduled source import</li>
<li>Validated PostgreSQL snapshot</li><li>Deterministic calculator</li>
<li>Cited result</li></ol>
<p>A calculator request never waits on a third-party service. If an import fails,
the previous verified snapshot remains available and is marked stale when it is too
old. If there is no safe observation, the result says unavailable.</p></section>

<section aria-labelledby="uses-heading"><h2 id="uses-heading">What each tool can learn from</h2>
<div class="table-wrap"><table class="data-table">
<thead><tr><th scope="col">Tool</th><th scope="col">Useful real data</th></tr></thead>
<tbody>
<tr><th scope="row">Hourly-rate floor</th><td>Paid DealFlow invoices divided by
TimeBank delivery hours, with project count and period.</td></tr>
<tr><th scope="row">Project estimate</th><td>Previous estimated versus actual hours,
accepted proposals, expenses and change orders.</td></tr>
<tr><th scope="row">Scope creep</th><td>Historical added hours, change-order value
and delivery delays.</td></tr>
<tr><th scope="row">Client fit</th><td>Payment lateness, disputes, repeat work,
cancellations and scope changes. This is not a credit score.</td></tr>
<tr><th scope="row">Cash flow</th><td>Invoices, milestones, due dates, recurring costs
and payment status.</td></tr>
<tr><th scope="row">Skill gap</th><td>ESCO occupation and skill concepts plus Growth
SkillTree evidence.</td></tr>
<tr><th scope="row">Cost context</th><td>Annual World Bank purchasing-power
observations, kept separate from exchange rates and market prices.</td></tr>
<tr><th scope="row">Tax and retirement</th><td>User-supplied scenarios until reviewed,
country-specific and effective-dated rule packs exist.</td></tr>
</tbody></table></div></section>

<section aria-labelledby="sources-heading"><h2 id="sources-heading">Deliberately limited public sources</h2>
<ul class="source-list">
<li><a href="https://datahelpdesk.worldbank.org/knowledgebase/articles/889392"
rel="external noopener">World Bank Indicators API</a> for annual economic context.
PPP is not a rate recommendation.</li>
<li><a href="https://esco.ec.europa.eu/en/use-esco"
rel="external noopener">ESCO</a> for maintained occupation and skill concepts.</li>
<li><a href="https://services.onetcenter.org/reference/start/overview"
rel="external noopener">O*NET Web Services</a> as optional US-specific enrichment
with required access and attribution.</li>
<li><a href="https://ilostat.ilo.org/data/bulk/"
rel="external noopener">ILOSTAT bulk data</a> for labour statistics—not freelance
prices.</li>
<li><a href="https://data.ecb.europa.eu/help/api/data"
rel="external noopener">ECB Data Portal API</a> for informational reference-rate
observations.</li>
</ul></section>

<section class="release-status" aria-labelledby="status-heading">
<h2 id="status-heading">What exists today</h2>
<p><strong>Available:</strong> deterministic calculators with explicit inputs and
formula versions. The PostgreSQL reference-data schema, a guarded World Bank import
job and a provenance API are implemented and tested.</p>
<p><strong>Not yet active in public results:</strong> live external observations,
personal DealFlow/TimeBank metrics, the pinned ESCO release and anonymous benchmarks.
No external observation is used until provider compatibility and freshness are verified.</p>
<p>Cross-customer benchmarks will require explicit consent and minimum cohort sizes.
Sparse groups return <strong>insufficient data</strong>—never a fabricated fallback.</p>
</section></article>""",
    )


@router.get("/tools/{slug}", response_class=HTMLResponse)
def tool(slug: str):
    if slug not in TOOLS:
        raise HTTPException(404, "Tool not found")
    title, description, model, methodology_copy = TOOLS[slug]
    schema = model.model_json_schema()
    controls = []
    for name, prop in schema["properties"].items():
        label = escape(name.replace("_", " ").capitalize())
        kind = prop.get("type", "string")
        default = prop.get("default", "")
        if isinstance(default, list):
            default = ", ".join(default)
        required = "required" if name in schema.get("required", []) else ""
        attrs = ""
        for key, attr in [
            ("minimum", "min"),
            ("maximum", "max"),
            ("pattern", "pattern"),
        ]:
            if key in prop:
                attrs += f' {attr}="{escape(str(prop[key]), quote=True)}"'
        input_type = "number" if kind in ("integer", "number") else "text"
        step = 'step="1"' if kind == "integer" else 'step="any"'
        controls.append(
            f'<label for="{name}">{label}</label><input id="{name}" name="{name}" '
            f'data-kind="{kind}" type="{input_type}" {step} {required}{attrs} '
            f'value="{escape(str(default), quote=True)}">'
        )
    return page(
        title,
        f'<a href="/tools">← All tools</a><h1>{escape(title)}</h1>'
        f"<p>{escape(description)}</p>"
        f'<div class="workbench"><form data-tool="{slug}">{"".join(controls)}'
        '<button type="submit">Calculate</button>'
        '<p id="status" role="status" aria-live="polite"></p></form>'
        '<section class="result" aria-labelledby="result-heading">'
        '<h2 id="result-heading">Your result</h2>'
        '<p id="empty">Enter your assumptions, then calculate.</p>'
        '<div id="result"></div><button id="download" type="button" hidden>'
        "Download result</button></section></div>"
        '<section class="method"><h2>How to read this result</h2>'
        f"<p>{escape(methodology_copy)}</p>"
        "<p>Review the assumptions before making a decision. Downloads contain your "
        "submitted inputs and result. DealFlow saving requires a configured workspace "
        "connection and an existing account. Skill-gap results remain download-only. "
        "Unsaved inputs are lost on page reload.</p>"
        '<p><a href="/methodology">How OSFreelance uses data →</a></p></section>',
    )
