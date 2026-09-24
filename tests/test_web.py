from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import create_app
from app.routes.web import router, TOOLS
from app.routes.estimates import router as estimates

app = FastAPI()
app.include_router(router)
app.include_router(estimates, prefix="/calculators")
client = TestClient(app)


def test_public_origin_serves_brand_homepage_not_obsolete_api_stub():
    response = TestClient(create_app()).get("/")

    assert response.status_code == 200
    assert "Make independent" in response.text
    assert 'href="/">OS<span>Freelance</span>' in response.text
    assert 'href="/tools/hourly-rate"' in response.text
    assert "Freelancer LeadTools API" not in response.text
    assert 'noindex, nofollow' not in response.text


def test_index_and_all_tool_forms():
    page = client.get("/tools")
    assert page.status_code == 200
    assert "noindex" not in page.text
    assert "/tool-assets/brand/favicon.svg" in page.text
    assert "/tool-assets/brand/apple-touch-icon.png" in page.text
    assert 'property="og:image"' in page.text
    assert "http://127.0.0.1:8091/tool-assets/brand/social-card.png" in page.text
    for slug in TOOLS:
        response = client.get("/tools/" + slug)
        assert response.status_code == 200
        assert 'data-tool="' + slug + '"' in response.text
        assert 'aria-live="polite"' in response.text
        assert "Download result" in response.text


def test_unknown_tool():
    assert client.get("/tools/not-a-tool").status_code == 404


def test_project_estimate():
    response = client.post(
        "/calculators/project-estimate",
        json={
            "hours": 10,
            "hourly_rate": 50,
            "expenses": 100,
            "contingency_percent": 10,
            "currency": "KES",
        },
    )
    assert response.status_code == 200
    assert response.json()["estimate"] == 660
    assert response.json()["formula_version"] == "project-estimate-v1"


def test_invalid_estimate():
    assert (
        client.post(
            "/calculators/project-estimate",
            json={"hours": -10, "hourly_rate": 50, "currency": "KES"},
        ).status_code
        == 422
    )


def test_brand_asset_formats_and_dimensions():
    brand = Path(__file__).parents[1] / "app" / "static" / "brand"
    assert (brand / "social-card.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert (brand / "favicon-32.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert (brand / "favicon.ico").read_bytes()[:4] == b"\x00\x00\x01\x00"
    assert 'viewBox="0 0 256 256"' in (brand / "osfreelance-mark.svg").read_text(
        encoding="utf-8"
    )
    assert "1200 630" in (brand / "social-card.svg").read_text(encoding="utf-8")


def test_index_explains_data_trust_boundary():
    response = client.get("/tools")

    assert response.status_code == 200
    assert "Real context, not invented benchmarks." in response.text
    assert 'href="/methodology"' in response.text
    assert "owner-authorized work history" in " ".join(response.text.split())
    assert "When available" in response.text


def test_public_data_methodology_is_truthful_and_cited():
    response = client.get("/methodology")

    assert response.status_code == 200
    assert "Scheduled source import" in response.text
    assert "Validated PostgreSQL snapshot" in response.text
    assert "World Bank Indicators API" in response.text
    assert "ESCO" in response.text
    assert "insufficient data" in response.text
    assert "Not yet active in public results" in response.text
    assert "No external observation is used until" in response.text
    assert "live market rate" not in response.text.lower()
