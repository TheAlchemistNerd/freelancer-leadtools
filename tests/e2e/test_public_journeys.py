"""Opt-in real-browser journeys. RUN_BROWSER_TESTS=1; browser must be installed.

Uses an isolated local API/SQLite database, never the user's database or providers.
PLAYWRIGHT_CHANNEL=msedge uses an existing Edge install; unset for bundled Chromium.
"""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in browser suite"
)

CASES = {
    "hourly-rate": {"target_annual_income": "60000"},
    "project-estimate": {
        "hours": "10",
        "hourly_rate": "50",
        "expenses": "100",
        "contingency_percent": "10",
        "currency": "KES",
    },
    "scope-creep": {
        "extra_requests_count": "2",
        "avg_hours_per_request": "3",
        "hourly_rate": "50",
        "delivery_delay_days": "2",
    },
    "client-fit": {
        "offered_budget": "5000",
        "proposed_timeline_days": "30",
        "scope_clarity_score": "4",
        "communication_quality_score": "4",
        "payment_reliability_signal": "4",
    },
    "cash-flow": {
        "current_cash": "10000",
        "accounts_receivable": "500",
        "accounts_payable": "100",
        "monthly_operating_expenses": "1000",
        "expected_new_revenue": "3000",
    },
    "skill-gap": {
        "target_role": "copywriter",
        "current_skills": "research",
        "experience_level": "junior",
        "target_skills": "research, editing",
    },
}


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    root = Path(__file__).resolve().parents[2]
    temp = tmp_path_factory.mktemp("web-server")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = dict(
        os.environ,
        DATABASE_URL="sqlite:///" + (temp / "test.db").as_posix(),
        ENVIRONMENT="development",
        RATE_LIMIT_ENABLED="false",
    )
    log = (temp / "server.log").open("w")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=root,
        env=env,
        stdout=log,
        stderr=log,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            if process.poll() is not None:
                pytest.fail("Test server exited; inspect " + str(temp / "server.log"))
            try:
                with urlopen(base + "/healthz", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.2)
        else:
            pytest.fail("Test server did not start")
        yield base
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        log.close()


@pytest.fixture
def page(tmp_path):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as runner:
        browser = runner.chromium.launch(
            headless=True, channel=os.getenv("PLAYWRIGHT_CHANNEL") or None
        )
        context = browser.new_context(accept_downloads=True)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        yield page
        page.screenshot(path=str(tmp_path / "final.png"), full_page=True)
        context.tracing.stop(path=str(tmp_path / "trace.zip"))
        context.close()
        browser.close()


@pytest.mark.parametrize("slug", CASES)
def test_calculate_export_and_invalidate(page, server, slug):
    from playwright.sync_api import expect

    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(server + "/tools/" + slug)
    expect(page.locator("#download")).to_be_hidden()
    for name, value in CASES[slug].items():
        page.locator("#" + name).fill(value)
    page.get_by_role("button", name="Calculate", exact=True).click()
    expect(page.locator("#status")).to_have_text("Result ready.")
    with page.expect_download() as received:
        page.get_by_role("button", name="Download result").click()
    data = json.loads(Path(received.value.path()).read_text())
    assert data["tool"] == slug
    if slug == "project-estimate":
        assert data["result"]["estimate"] == 660
    if slug == "scope-creep":
        assert data["result"]["delay_cost"] == 0
    if slug == "skill-gap":
        assert data["result"]["gaps"] == ["editing"]
    first = next(iter(CASES[slug]))
    page.locator("#" + first).fill(CASES[slug][first] + "0")
    expect(page.locator("#download")).to_be_hidden()
    expect(page.locator("#result")).to_be_empty()
    assert not errors


def test_public_origin_opens_brand_homepage_and_tool(page, server):
    from playwright.sync_api import expect

    page.goto(server + "/")
    expect(page.get_by_role("heading", level=1)).to_contain_text(
        "Make independent"
    )
    expect(page.locator('a.brand[href="/"]')).to_be_visible()
    page.locator('a[href="/tools/project-estimate"]').click()
    expect(page).to_have_url(server + "/tools/project-estimate")
    expect(page.get_by_role("heading", level=1)).to_have_text("Price a project")


def test_mobile_and_keyboard_navigation(page, server):
    from playwright.sync_api import expect

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(server + "/tools")
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.get_by_role("link", name="FREE TOOL Price a project", exact=False).click()
    expect(
        page.get_by_role("heading", name="Price a project", exact=True)
    ).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_server_validation_and_retry(page, server):
    from playwright.sync_api import expect

    page.goto(server + "/tools/project-estimate")
    for name, value in CASES["project-estimate"].items():
        page.locator("#" + name).fill(value)
    page.route(
        "**/calculators/project-estimate",
        lambda route: route.fulfill(
            status=422,
            content_type="application/json",
            body=json.dumps(
                {"detail": [{"loc": ["body", "hours"], "msg": "Invalid hours"}]}
            ),
        ),
    )
    page.get_by_role("button", name="Calculate", exact=True).click()
    expect(page.locator("#status")).to_contain_text("hours: Invalid hours")
    expect(page.locator("#download")).to_be_hidden()
    page.unroute("**/calculators/project-estimate")
    page.get_by_role("button", name="Calculate", exact=True).click()
    expect(page.locator("#status")).to_have_text("Result ready.")


def test_workspace_ui_confirmation_retry_and_signout(page, server):
    """Real UI/API calculation; workspace responses are explicit browser mocks."""
    from playwright.sync_api import expect

    saves = []
    logins = []

    def login(route):
        logins.append(route.request.post_data_json)
        route.fulfill(
            status=200, content_type="application/json", body='{"signed_in":true}'
        )

    def save(route):
        saves.append(route.request.post_data_json)
        if len(saves) == 1:
            route.fulfill(
                status=503,
                content_type="application/json",
                body='{"detail":"Retry saving"}',
            )
        else:
            route.fulfill(
                status=201,
                content_type="application/json",
                body='{"id":"saved-example"}',
            )

    page.route("**/workspace/login", login)
    page.route("**/workspace/tool-results", save)
    page.route(
        "**/workspace/tool-results?offset=0",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "items": [
                        {
                            "id": "saved-example",
                            "created_at": "2026-09-19T12:00:00Z",
                            "snapshot": {
                                "tool": "project-estimate",
                                "inputs": {"hours": 10},
                                "result": {"estimate": 660},
                            },
                        }
                    ]
                }
            ),
        ),
    )
    page.route(
        "**/workspace/logout",
        lambda route: route.fulfill(
            status=200, content_type="application/json", body='{"signed_in":false}'
        ),
    )
    page.goto(server + "/tools/project-estimate")
    for name, value in CASES["project-estimate"].items():
        page.locator("#" + name).fill(value)
    page.get_by_role("button", name="Calculate", exact=True).click()
    page.get_by_role("button", name="Save to DealFlow").click()
    page.get_by_role("button", name="Confirm save").click()
    expect(page.locator("#workspace-status")).to_contain_text("Confirm that")
    assert not saves
    page.locator("#workspace-email").fill("test@example.com")
    page.locator("#workspace-password").fill("synthetic-password")
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page.locator("#workspace-status")).to_contain_text("Signed in")
    expect(page.locator("#workspace-password")).to_have_value("")
    expect(page.locator("#hours")).to_have_value("10")
    page.locator("#save-consent").check()
    page.get_by_role("button", name="Confirm save").click()
    expect(page.locator("#workspace-status")).to_have_text("Retry saving")
    page.get_by_role("button", name="Confirm save").click()
    expect(page.locator("#workspace-status")).to_contain_text("saved-example")
    assert saves[0] == saves[1]
    assert saves[0]["confirmed"] is True
    assert saves[0]["result"]["estimate"] == 660
    assert len(logins) == 1
    assert page.evaluate("localStorage.length === 0 && sessionStorage.length === 0")
    page.get_by_role("button", name="View saved results").click()
    expect(page.locator("#workspace-status")).to_have_text("Showing 1 saved results.")
    page.locator("#saved-results summary").click()
    expect(page.locator("#saved-results pre")).to_contain_text('"estimate": 660')
    page.get_by_role("button", name="Sign out", exact=True).click()
    expect(page.locator("#workspace-status")).to_contain_text("Signed out")
    expect(page.locator("#saved-results")).to_be_empty()
    page.locator("#hours").fill("11")
    expect(page.get_by_role("button", name="Save to DealFlow")).to_be_hidden()
    expect(page.locator("#save-consent")).not_to_be_checked()


def test_data_methodology_journey(page, server):
    from playwright.sync_api import expect

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(server + "/tools")
    page.get_by_role("link", name="See how our data works").click()

    expect(page).to_have_url(server + "/methodology")
    expect(
        page.get_by_role("heading", name="Useful numbers should be explainable.")
    ).to_be_visible()
    expect(
        page.get_by_text("Validated PostgreSQL snapshot", exact=True)
    ).to_be_visible()
    expect(
        page.get_by_role("link", name="World Bank Indicators API")
    ).to_have_attribute(
        "href", "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392"
    )
    expect(
        page.get_by_text("Not yet active in public results:", exact=False)
    ).to_be_visible()
    expect(page.get_by_text("insufficient data", exact=True)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
