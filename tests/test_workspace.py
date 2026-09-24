import json
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes import workspace as w
from freelancer_core.reliability.xss import XSSProtectionMiddleware


@pytest.fixture
def gateway(monkeypatch):
    monkeypatch.setattr(w.settings, "identity_api_url", "http://127.0.0.1:8100")
    monkeypatch.setattr(w.settings, "workspace_dealflow_url", "http://127.0.0.1:8101")
    monkeypatch.setattr(w.settings, "web_public_origin", "http://testserver")
    monkeypatch.setattr(w.settings, "environment", "development")
    # Only loopback HTTP is allowed, including the public origin.
    monkeypatch.setattr(w.settings, "web_public_origin", "http://localhost")
    data = {}
    redis = AsyncMock()
    redis.get.side_effect = lambda key: data.get(key)
    redis.getdel.side_effect = lambda key: data.pop(key, None)
    redis.delete.side_effect = lambda key: data.pop(key, None)
    redis.set.side_effect = lambda key, value, ex: data.__setitem__(key, value)
    monkeypatch.setattr(w, "redis_client", AsyncMock(return_value=redis))
    upstream = AsyncMock()
    upstream.request.return_value = httpx.Response(200, json={"access_token": "private-token"})
    app = FastAPI()
    app.add_middleware(XSSProtectionMiddleware, excluded_paths=("/workspace/login", "/workspace/register"))
    app.include_router(w.router)
    app.dependency_overrides[w.upstream] = lambda: upstream
    with TestClient(app, base_url="http://localhost", headers={"Origin": "http://localhost"}) as client:
        yield client, upstream, redis, data


def sign_in(client):
    return client.post("/workspace/login", json={"email": "user@example.com", "password": "password1234"})


def test_private_cookie_session_and_save(gateway):
    client, upstream, redis, data = gateway
    response = sign_in(client)
    assert response.status_code == 200
    assert "private-token" not in response.text
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie and "Path=/workspace" in cookie
    assert response.headers["cache-control"] == "no-store"
    assert "password1234" not in json.dumps(data)
    assert redis.set.call_args.kwargs["ex"] == 900
    upstream.request.return_value = httpx.Response(201, json={"id": "saved-123"})
    response = client.post("/workspace/tool-results", json={"confirmed": True})
    assert response.status_code == 201
    assert upstream.request.call_args.kwargs["headers"] == {"Authorization": "Bearer private-token"}
    assert upstream.request.call_args.args[1] == "http://127.0.0.1:8101/api/v1/tool-results"


def test_password_is_forwarded_verbatim_not_html_filtered(gateway):
    client, upstream, _, _ = gateway
    password = "valid-onclick=<script>password</script>"
    response = client.post("/workspace/login", json={"email": "user@example.com", "password": password})
    assert response.status_code == 200
    assert upstream.request.call_args.kwargs["data"]["password"] == password


def test_cross_origin_and_expiry_are_denied(gateway):
    client, upstream, redis, data = gateway
    response = client.post("/workspace/login", headers={"Origin": "https://attacker.example"}, json={})
    assert response.status_code == 403
    assert not upstream.request.called
    assert client.post("/workspace/tool-results", json={}).status_code == 401
    assert sign_in(client).status_code == 200
    data.clear()
    assert client.post("/workspace/tool-results", json={}).status_code == 401


def test_logout_deletes_session_and_revokes_upstream(gateway):
    client, upstream, redis, data = gateway
    sign_in(client)
    upstream.request.return_value = httpx.Response(200, json={"message": "logged out"})
    assert client.post("/workspace/logout").status_code == 200
    assert not data
    assert client.post("/workspace/tool-results", json={}).status_code == 401


def test_saved_results_require_session_and_bound_pagination(gateway):
    client, upstream, redis, data = gateway
    assert client.get("/workspace/tool-results").status_code == 401
    sign_in(client)
    upstream.request.return_value = httpx.Response(200, json={"items": []})
    response = client.get("/workspace/tool-results?offset=20")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert upstream.request.call_args.kwargs["params"] == {"limit": 20, "offset": 20}
    assert upstream.request.call_args.kwargs["headers"] == {"Authorization": "Bearer private-token"}
    assert client.get("/workspace/tool-results?offset=-1").status_code == 422


def test_registration_is_validated_and_does_not_issue_session(gateway):
    client, upstream, redis, data = gateway
    payload = {"email": "new@example.com", "password": "long<script>password"}
    assert client.post("/workspace/register", json={**payload, "role": "admin"}).status_code == 422
    assert client.post("/workspace/register", json={**payload, "password": "short"}).status_code == 422
    upstream.request.assert_not_called()
    upstream.request.return_value = httpx.Response(201, json={"id": "new-user"})
    response = client.post("/workspace/register", json=payload)
    assert response.status_code == 201 and response.json() == {"registered": True}
    assert "set-cookie" not in response.headers and not data
    assert upstream.request.call_args.kwargs["json"] == payload
    upstream.request.return_value = httpx.Response(409, json={})
    assert "signing in" in client.post("/workspace/register", json=payload).json()["detail"]


def test_production_rejects_http_and_uses_secure_cookie(gateway, monkeypatch):
    client, upstream, redis, data = gateway
    monkeypatch.setattr(w.settings, "environment", "production")
    assert sign_in(client).status_code == 503
    monkeypatch.setattr(w.settings, "identity_api_url", "https://identity.example")
    monkeypatch.setattr(w.settings, "workspace_dealflow_url", "https://dealflow.example")
    monkeypatch.setattr(w.settings, "web_public_origin", "https://osfreelance.com")
    client.headers["Origin"] = "https://osfreelance.com"
    assert "Secure" in sign_in(client).headers["set-cookie"]


def test_proposal_workspace_page_is_public_but_private_data_requires_session(gateway):
    client, upstream, _, _ = gateway
    page = client.get("/workspace")
    assert page.status_code == 200
    assert page.headers["cache-control"] == "no-store"
    assert "Proposal drafts" in page.text
    assert "private-token" not in page.text
    assert client.get("/workspace/proposals").status_code == 401
    upstream.request.assert_not_called()


def test_proposal_gateway_keeps_tokens_and_tracking_data_server_side(gateway):
    client, upstream, _, _ = gateway
    assert sign_in(client).status_code == 200
    upstream.request.return_value = httpx.Response(201, json={
        "id": "proposal-1", "title": "Client portal", "client_name": "Example client",
        "client_email": "client@example.com", "status": "Draft",
        "created_at": "2026-09-24T00:00:00Z", "tracking_token": "secret-tracker",
        "content": {"summary": "Private scope"},
    })
    payload = {"title": "Client portal", "client_name": "Example client",
               "client_email": "client@example.com", "summary": "Build the portal."}
    response = client.post("/workspace/proposals", json=payload)
    assert response.status_code == 201
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"id": "proposal-1", "title": "Client portal",
                               "client_name": "Example client", "status": "Draft",
                               "created_at": "2026-09-24T00:00:00Z"}
    assert "secret-tracker" not in response.text
    assert upstream.request.call_args.args[:2] == (
        "POST", "http://127.0.0.1:8101/api/v1/proposals/")
    assert upstream.request.call_args.kwargs["headers"] == {
        "Authorization": "Bearer private-token"}
    assert upstream.request.call_args.kwargs["json"]["content"] == {
        "summary": "Build the portal.", "source": "user-authored"}
    assert client.post("/workspace/proposals", headers={"Origin": "https://evil.example"},
                       json=payload).status_code == 403
    assert client.post("/workspace/proposals", json={**payload, "client_email": "bad"}).status_code == 422

    upstream.request.return_value = httpx.Response(200, json={
        "items": [{"id": "proposal-1", "title": "Client portal",
                   "client_name": "Example client", "status": "Draft",
                   "created_at": "2026-09-24T00:00:00Z",
                   "tracking_token": "secret-tracker", "content": {"summary": "Private scope"}}],
        "page": 1, "pages": 1,
    })
    listing = client.get("/workspace/proposals")
    assert listing.status_code == 200
    assert listing.json()["items"] == [response.json()]
    assert "secret-tracker" not in listing.text
    assert upstream.request.call_args.kwargs["params"] == {"page": 1, "size": 20}
