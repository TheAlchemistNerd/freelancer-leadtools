"""Fixed-destination browser gateway; never expose bearer tokens to JavaScript."""
import hashlib
import json
import secrets
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from redis.exceptions import RedisError
from freelancer_core.reliability.redis import RedisFactory
from app.config import settings
from app.routes.web import page

COOKIE = "osf_workspace"
SESSION_SECONDS = 900


def configured():
    urls = [settings.identity_api_url, settings.workspace_dealflow_url, settings.web_public_origin]
    if not all(urls):
        raise HTTPException(503, "Workspace sign-in is not configured yet.")
    for url in urls:
        parsed = urlsplit(url)
        local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if (parsed.username or parsed.password or parsed.query or parsed.fragment
                or not parsed.netloc or parsed.scheme not in {"http", "https"}
                or (parsed.scheme != "https" and not (settings.is_development and local))):
            raise HTTPException(503, "Workspace URL configuration is unsafe.")


async def browser_boundary(request: Request):
    configured()
    if request.method != "GET" and request.headers.get("origin") != settings.web_public_origin:
        raise HTTPException(403, "Same-origin request required.")


router = APIRouter(prefix="/workspace", dependencies=[Depends(browser_boundary)])


async def upstream():
    async with httpx.AsyncClient(timeout=15, follow_redirects=False, trust_env=False) as client:
        yield client


def session_key(value):
    return "leadtools:web-session:" + hashlib.sha256(value.encode()).hexdigest()


async def redis_client():
    try:
        client = await RedisFactory.get_client()
    except (RedisError, OSError):
        raise HTTPException(503, "Workspace session storage unavailable. Please retry.") from None
    if client is None:
        raise HTTPException(503, "Workspace session storage unavailable.")
    return client


async def session(request: Request):
    cookie = request.cookies.get(COOKIE, "")
    if len(cookie) != 43:
        raise HTTPException(401, "Sign in to save this result.")
    redis = await redis_client()
    raw = await redis.get(session_key(cookie))
    if not raw:
        raise HTTPException(401, "Session expired. Sign in again; your result is still here.")
    return json.loads(raw)


async def call(client, method, url, conflict_detail="This save request conflicts with an earlier result.", **kwargs):
    try:
        response = await client.request(method, url, **kwargs)
    except httpx.RequestError:
        raise HTTPException(503, "Workspace service unavailable. Please retry.") from None
    if response.status_code in (401, 403):
        raise HTTPException(response.status_code, "Sign-in failed or your session expired.")
    if response.status_code == 409:
        raise HTTPException(409, conflict_detail)
    if response.status_code == 422:
        raise HTTPException(422, "Check the supplied details and try again.")
    if not 200 <= response.status_code < 300:
        raise HTTPException(503, "Workspace service unavailable. Please retry.")
    try:
        payload = response.json()
    except ValueError:
        raise HTTPException(503, "Workspace returned an invalid response.") from None
    if not isinstance(payload, dict):
        raise HTTPException(503, "Workspace returned an invalid response.")
    return payload


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class Signup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class ProposalDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3, max_length=200)
    client_name: str = Field(min_length=1, max_length=200)
    client_email: EmailStr
    summary: str = Field(min_length=1, max_length=5000)


class DocumentSection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    heading: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=10000)


class DocumentSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    template: Literal["proposal-v1", "contract-v1"]
    format: Literal["docx", "pdf"]
    title: str = Field(min_length=1, max_length=200)
    client_name: str = Field(min_length=1, max_length=200)
    author_name: str = Field(min_length=1, max_length=200)
    sections: list[DocumentSection] = Field(min_length=1, max_length=20)

    @field_validator("sections")
    @classmethod
    def bound_content(cls, sections):
        if sum(len(section.body) for section in sections) > 50000:
            raise ValueError("Document content exceeds 50000 characters")
        return sections


class AIDraftSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document: DocumentSubmission
    brief: str = Field(min_length=1, max_length=20000)
    consent_to_provider: Literal[True]


class DraftAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    acknowledge_missing_information: bool = False


def public_proposal(item: dict) -> dict:
    """Only browser-safe fields; never expose tracking tokens or raw content."""
    required = ("id", "title", "client_name", "status", "created_at")
    if not isinstance(item, dict) or any(key not in item for key in required):
        raise HTTPException(503, "Workspace returned an invalid proposal.")
    return {key: item[key] for key in required}


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def workspace_page():
    response = page(
        "Your workspace",
        '<section class="method"><p class="eyebrow">PRIVATE WORKSPACE</p>'
        '<h1>Move from estimate to proposal.</h1>'
        '<p>Draft a proposal and review it before any delivery. Creating a draft does '
        'not send it, request a signature or charge a client.</p></section>'
        '<section id="workspace-signin" class="method" aria-labelledby="signin-heading">'
        '<h2 id="signin-heading">Sign in</h2>'
        '<form id="workspace-auth-form"><label for="workspace-email">Email</label>'
        '<input id="workspace-email" type="email" autocomplete="username" required>'
        '<label for="workspace-password">Password</label>'
        '<input id="workspace-password" type="password" autocomplete="current-password" required>'
        '<button type="submit">Sign in</button></form>'
        '<p>New here? <a href="/tools">Use a free tool and create an account there.</a></p></section>'
        '<section id="workspace-private" class="method" hidden>'
        '<h2>Proposal drafts</h2><p>Keep client details factual. These drafts remain '
        'private until you deliberately use a separate delivery workflow.</p>'
        '<form id="proposal-form"><label for="proposal-title">Title</label>'
        '<input id="proposal-title" required maxlength="200">'
        '<label for="proposal-client">Client name</label>'
        '<input id="proposal-client" required maxlength="200">'
        '<label for="proposal-email">Client email</label>'
        '<input id="proposal-email" type="email" required>'
        '<label for="proposal-summary">Summary</label>'
        '<textarea id="proposal-summary" required maxlength="5000" rows="6"></textarea>'
        '<button type="submit">Save proposal draft</button></form>'
        '<h3>Your proposals</h3><ul id="proposal-list"></ul>'
        '<section class="workspace-documents" aria-labelledby="documents-heading">'
        '<p class="eyebrow">DOCUMENT STUDIO</p><h2 id="documents-heading">Prepare a document</h2>'
        '<p>Create a proposal or contract file from your own text. OpenRouter can '
        'draft proposal sections for review; for contracts it may draft only an '
        'introduction. Neither path '
        'sends a contract, requests a signature or charges anyone.</p>'
        '<form id="document-form">'
        '<label for="document-template">Document type</label>'
        '<select id="document-template"><option value="proposal-v1">Proposal</option>'
        '<option value="contract-v1">Contract</option></select>'
        '<label for="document-format">Export format</label>'
        '<select id="document-format"><option value="pdf">PDF</option>'
        '<option value="docx">Word DOCX</option></select>'
        '<label for="document-title">Title</label>'
        '<input id="document-title" required maxlength="200">'
        '<label for="document-client">Client name</label>'
        '<input id="document-client" required maxlength="200">'
        '<label for="document-author">Your name</label>'
        '<input id="document-author" required maxlength="200">'
        '<label for="document-body">Existing text or terms to preserve</label>'
        '<textarea id="document-body" required maxlength="10000" rows="8"></textarea>'
        '<p>When AI is enabled, this text is not sent to OpenRouter and remains '
        'unchanged in the rendered file. Put only information you consent to share '
        'in the separate brief.</p>'
        '<label class="check-row" for="document-ai"><input id="document-ai" type="checkbox">'
        ' Ask AI to draft proposal sections (contract: introduction only)</label>'
        '<div id="document-ai-fields" hidden>'
        '<label for="document-brief">Brief for OpenRouter</label>'
        '<textarea id="document-brief" maxlength="20000" rows="5"></textarea>'
        '<label class="check-row" for="document-consent">'
        '<input id="document-consent" type="checkbox"> I consent to sending this brief '
        'to OpenRouter for this draft.</label>'
        '<p>Keep secrets and sensitive client details out of the brief. AI cannot '
        'set prices, payment terms or contract clauses. Review the complete draft '
        'before acceptance.</p></div>'
        '<button type="submit">Prepare document</button></form>'
        '<p id="document-status" role="status" aria-live="polite"></p>'
        '<section id="draft-review" class="result" aria-labelledby="draft-review-heading" hidden>'
        '<h3 id="draft-review-heading">Review complete document</h3>'
        '<div id="draft-content"></div><ul id="draft-missing"></ul>'
        '<label class="check-row" for="draft-acknowledge" id="draft-acknowledge-row" hidden>'
        '<input id="draft-acknowledge" type="checkbox"> I reviewed the missing information.</label>'
        '<button id="draft-accept" type="button">Accept and render this version</button>'
        '</section><h3>Your document jobs</h3><ul id="document-list"></ul></section>'
        '<button id="workspace-signout" type="button">Sign out</button></section>'
        '<p id="workspace-page-status" role="status" aria-live="polite"></p>'
        '<script defer src="/tool-assets/workspace.js"></script>',
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/register", status_code=201)
async def register(payload: Signup, response: Response, client=Depends(upstream)):
    await call(client, "POST", settings.identity_api_url.rstrip("/") + "/api/v1/auth/register",
               json=payload.model_dump(),
               conflict_detail="An account with these details may already exist. Try signing in.")
    response.headers["Cache-Control"] = "no-store"
    # Account creation is separate from sign-in. Never imply a session was issued.
    return {"registered": True}


@router.post("/login")
async def login(payload: Login, request: Request, response: Response, client=Depends(upstream)):
    tokens = await call(client, "POST", settings.identity_api_url.rstrip("/") + "/api/v1/auth/login",
                        data={"username": payload.email, "password": payload.password})
    access = tokens.get("access_token")
    if not isinstance(access, str) or not access:
        raise HTTPException(503, "Identity returned an invalid response.")
    redis = await redis_client()
    old = request.cookies.get(COOKIE)
    if old:
        await redis.delete(session_key(old))
    cookie = secrets.token_urlsafe(32)
    # No password or refresh token is retained. Reauthentication is explicit.
    await redis.set(session_key(cookie), json.dumps({"access_token": access}), ex=SESSION_SECONDS)
    response.set_cookie(COOKIE, cookie, max_age=SESSION_SECONDS, httponly=True,
                        secure=not settings.is_development, samesite="strict", path="/workspace")
    response.headers["Cache-Control"] = "no-store"
    return {"signed_in": True, "expires_in": SESSION_SECONDS}


@router.post("/logout")
async def logout(request: Request, response: Response, client=Depends(upstream)):
    cookie = request.cookies.get(COOKIE, "")
    redis = await redis_client()
    raw = await redis.getdel(session_key(cookie)) if cookie else None
    if raw:
        await call(client, "POST", settings.identity_api_url.rstrip("/") + "/api/v1/auth/logout",
                   headers={"Authorization": "Bearer " + json.loads(raw)["access_token"]})
    response.delete_cookie(COOKIE, path="/workspace")
    response.headers["Cache-Control"] = "no-store"
    return {"signed_in": False}


@router.post("/tool-results", status_code=201)
async def save_result(payload: dict, response: Response, auth=Depends(session), client=Depends(upstream)):
    result = await call(client, "POST", settings.workspace_dealflow_url.rstrip("/") + "/api/v1/tool-results",
                        headers={"Authorization": "Bearer " + auth["access_token"]}, json=payload)
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("/tool-results")
async def saved_results(response: Response, offset: int = Query(0, ge=0),
                        auth=Depends(session), client=Depends(upstream)):
    result = await call(client, "GET", settings.workspace_dealflow_url.rstrip("/") + "/api/v1/tool-results",
                        headers={"Authorization": "Bearer " + auth["access_token"]},
                        params={"limit": 20, "offset": offset})
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("/proposals")
async def list_proposals(response: Response, page_number: int = Query(1, ge=1, le=1000),
                         auth=Depends(session), client=Depends(upstream)):
    result = await call(
        client, "GET", settings.workspace_dealflow_url.rstrip("/") + "/api/v1/proposals/",
        headers={"Authorization": "Bearer " + auth["access_token"]},
        params={"page": page_number, "size": 20},
    )
    if not isinstance(result.get("items"), list):
        raise HTTPException(503, "Workspace returned an invalid proposal list.")
    response.headers["Cache-Control"] = "no-store"
    return {"items": [public_proposal(item) for item in result["items"]],
            "page": result.get("page"), "pages": result.get("pages")}


@router.post("/proposals", status_code=201)
async def create_proposal(payload: ProposalDraft, response: Response,
                          auth=Depends(session), client=Depends(upstream)):
    result = await call(
        client, "POST", settings.workspace_dealflow_url.rstrip("/") + "/api/v1/proposals/",
        headers={"Authorization": "Bearer " + auth["access_token"]},
        json={"title": payload.title, "client_name": payload.client_name,
              "client_email": str(payload.client_email),
              "content": {"summary": payload.summary, "source": "user-authored"}},
    )
    response.headers["Cache-Control"] = "no-store"
    return public_proposal(result)


def dealflow_url(path: str) -> str:
    return settings.workspace_dealflow_url.rstrip("/") + "/api/v1/documents/" + path


def bearer(auth: dict) -> dict[str, str]:
    return {"Authorization": "Bearer " + auth["access_token"]}


def private_response(response: Response, result: dict) -> dict:
    response.headers["Cache-Control"] = "no-store"
    return result


@router.post("/documents/jobs", status_code=202)
async def submit_document(payload: DocumentSubmission, response: Response,
                          auth=Depends(session), client=Depends(upstream)):
    result = await call(client, "POST", dealflow_url("jobs"),
                        headers=bearer(auth), json=payload.model_dump(mode="json"))
    return private_response(response, result)


@router.get("/documents/jobs")
async def document_jobs(response: Response, auth=Depends(session), client=Depends(upstream)):
    result = await call(client, "GET", dealflow_url("jobs"),
                        headers=bearer(auth), params={"limit": 20, "offset": 0})
    if not isinstance(result.get("items"), list):
        raise HTTPException(503, "Workspace returned an invalid document list.")
    return private_response(response, {"items": result["items"]})


@router.get("/documents/jobs/{job_id}")
async def document_job(job_id: UUID, response: Response,
                       auth=Depends(session), client=Depends(upstream)):
    result = await call(client, "GET", dealflow_url(f"jobs/{job_id}"), headers=bearer(auth))
    return private_response(response, result)


@router.get("/documents/jobs/{job_id}/download")
async def document_download(job_id: UUID, auth=Depends(session), client=Depends(upstream)):
    try:
        result = await client.request("GET", dealflow_url(f"jobs/{job_id}/download"),
                                      headers=bearer(auth))
    except httpx.RequestError:
        raise HTTPException(503, "Workspace service unavailable. Please retry.") from None
    if result.status_code in (401, 403, 404, 409, 410):
        raise HTTPException(result.status_code, "Document is unavailable or not ready.")
    if result.status_code != 200 or len(result.content) > 5 * 1024 * 1024:
        raise HTTPException(503, "Document download is unavailable.")
    media = result.headers.get("content-type", "").split(";", 1)[0].strip()
    extensions = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    }
    if media not in extensions:
        raise HTTPException(503, "Document download has an unexpected format.")
    return Response(
        result.content, media_type=media,
        headers={"Cache-Control": "no-store",
                 "Content-Disposition": f'attachment; filename="document-{job_id}.{extensions[media]}"',
                 "X-Content-Type-Options": "nosniff"},
    )


@router.post("/documents/drafts", status_code=202)
async def submit_ai_draft(payload: AIDraftSubmission, response: Response,
                          auth=Depends(session), client=Depends(upstream)):
    result = await call(
        client, "POST", dealflow_url("drafts"), headers=bearer(auth),
        json={**payload.model_dump(mode="json"), "provider": "openrouter"},
    )
    return private_response(response, result)


@router.get("/documents/drafts/{job_id}")
async def document_draft(job_id: UUID, response: Response,
                         auth=Depends(session), client=Depends(upstream)):
    result = await call(client, "GET", dealflow_url(f"drafts/{job_id}"), headers=bearer(auth))
    # The upstream contains the owner's frozen document brief. Return only the
    # review fields needed by this page, never worker or provider internals.
    safe = {key: result[key] for key in
            ("id", "status", "error_code", "draft", "review_sections", "sha256")
            if key in result}
    return private_response(response, safe)


@router.post("/documents/drafts/{job_id}/accept", status_code=202)
async def accept_ai_draft(job_id: UUID, payload: DraftAcceptance, response: Response,
                          auth=Depends(session), client=Depends(upstream)):
    result = await call(client, "POST", dealflow_url(f"drafts/{job_id}/accept"),
                        headers=bearer(auth), json=payload.model_dump())
    return private_response(response, result)
