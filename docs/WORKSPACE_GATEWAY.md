# Browser workspace gateway

The existing public calculator pages now offer an optional DealFlow save flow.
Skill-gap remains download-only until the Growth handoff is implemented.
This is an implementation increment, not verified production integration.

Configure these server-side environment variables (no API keys in JavaScript):

- `WEB_PUBLIC_ORIGIN`: exact browser origin, with no trailing slash or path.
- `IDENTITY_API_URL`: Identity service base URL, without `/api/v1`.
- `WORKSPACE_DEALFLOW_URL`: DealFlow base URL, without `/api/v1`.
- `REDIS_URL`: private session storage, also used by existing infrastructure.

HTTPS is required outside development. Development HTTP is restricted to loopback
hostnames. Missing configuration fails closed with 503; public calculations still
work. The existing `dealflow_api_url` property serves marketing URL construction
and is not this gateway's destination configuration.

POST `/workspace/register` accepts only email and a password of at least 12
characters, then delegates account creation to Identity. Callers cannot select a
role or tenant. Successful registration does not create a browser session; the
user deliberately re-enters the password and signs in. Existing-account conflicts
are returned as a safe prompt to sign in, without reflecting credentials.
POST `/workspace/login` accepts email/password and delegates authentication to
Identity. The random HttpOnly, SameSite=Strict cookie contains no bearer token.
Production cookies are Secure. Redis holds the access token under a hashed random
session key for at most 15 minutes. Passwords and refresh tokens are not retained;
reauthentication is required on expiration. Persistent/refreshable sessions are
still future work within the release's complete session journey.

All mutations require an Origin exactly matching WEB_PUBLIC_ORIGIN. The gateway
has fixed upstream destinations, disables redirect-following and uses bounded
HTTP timeouts. The Redis instance must remain private and protected; bearer tokens
are sensitive even though session IDs are hashed. Never log request bodies for
login or authorization headers. Passwords bypass the heuristic HTML input filter;
they must never be rendered into HTML.

Saving requires explicit consent. The browser keeps a stable request ID across
retries; DealFlow enforces owner/tenant isolation and idempotency. Inputs and the
result remain in page memory, not localStorage/sessionStorage. Editing calculator
inputs invalidates the result and resets consent. A page reload discards unsaved
inputs. Logout removes local Redis state and requests Identity revocation.

The workspace can be opened without calculating a new result. GET
`/workspace/tool-results?offset=0` retrieves 20 owner-scoped saved snapshots;
subsequent pages increment the offset. The gateway requires the session cookie,
passes only the server-held bearer token, and marks responses no-store. The UI
renders saved content as text, labels it unverified and clears it on sign-out or
account changes. Saved-result retrieval is not conversion into a proposal.

## Document studio

The branded `/workspace` now includes a document form and job list. A signed-in
user can submit a validated `proposal-v1` or `contract-v1` structure for DOCX/PDF
rendering, or explicitly consent to an OpenRouter-only introductory draft. The
browser never receives provider or bearer credentials. A completed AI draft is
shown as literal text with missing-information flags; acceptance sends its exact
SHA-256 to DealFlow and queues rendering. A document created this way is a draft
file, not an approved, sent or signed contract.

The fixed-destination gateway proxies owner-scoped job status and a bounded
download with a generated filename, allowed PDF/DOCX content types and no-store
headers. The rendered file is held by DealFlow's document job until object
storage and retention policies are finished. Session expiry requires sign-in
again; jobs remain in the owner's list. Live OpenRouter connectivity and the
post-render approval/signing flow are separate release gates.

Unit tests use mocked upstreams/Redis. The browser workspace test mocks the gateway
responses while exercising the actual calculator API. Neither proves the three
services work together. Full PostgreSQL/Redis/JWT integration for account creation, sign-in, save, retrieve
and logout has passed locally. Recovery, refresh policy and Growth handoff remain
gates. A separate real-service runner verifies that browser flow against migrated
PostgreSQL and real Redis; see root `docs/internal/workspace-stack-verification.md`.
