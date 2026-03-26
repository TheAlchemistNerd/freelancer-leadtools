# Freelancer LeadTools - Security Architecture

**Classification:** Internal - Engineering  
**Last Updated:** 2026-03-26  
**Owner:** Engineering Team  

---

## Overview

Freelancer LeadTools is a **public API** (no authentication required) that implements comprehensive web security measures to prevent abuse while maintaining accessibility.

### Security Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REQUEST FLOW WITH SECURITY                          │
└─────────────────────────────────────────────────────────────────────────────┘

Client Request
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. Request Size Limit Middleware                                           │
│     → Reject payloads > 1MB                                                 │
│     → Prevents DoS via large requests                                       │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. Bot Protection Middleware                                               │
│     → Analyze User-Agent                                                    │
│     → Block known bad bots (scrapers, scrapers)                            │
│     → Allow good bots (Googlebot, Bingbot)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. Rate Limiting Middleware (Redis-backed)                                 │
│     → Sliding window algorithm                                              │
│     → 100 requests/minute per IP (configurable)                            │
│     → Returns 429 with Retry-After header                                  │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. XSS Protection Middleware                                               │
│     → Sanitize query parameters                                            │
│     → Sanitize JSON body                                                   │
│     → Detect: <script>, javascript:, on*=handlers, etc.                    │
│     → Returns 400 on detection                                              │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. CSRF Protection Middleware                                              │
│     → Check Origin/Referer headers                                         │
│     → Validate CSRF tokens (for forms)                                     │
│     → Allow API key authentication                                         │
│     → Exempt public GET endpoints                                          │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  6. Application Logic                                                       │
│     → Calculator endpoints (public)                                        │
│     → Lead capture (with validation)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  7. Security Headers Middleware (Response)                                  │
│     → X-Content-Type-Options: nosniff                                      │
│     → X-Frame-Options: DENY                                                │
│     → X-XSS-Protection: 1; mode=block                                      │
│     → Referrer-Policy: strict-origin-when-cross-origin                     │
│     → Permissions-Policy: (restrict features)                              │
│     → Content-Security-Policy: (restrict resources)                        │
│     → Cache-Control: no-store (for API)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
Response to Client
```

---

## Security Features

### 1. Rate Limiting (HIGH PRIORITY ✅)

**Implementation:** Redis-backed sliding window

**Configuration:**
```bash
RATE_LIMIT_REQUESTS=100        # Max requests per window
RATE_LIMIT_WINDOW_SECONDS=60   # Window size
REDIS_URL=redis://localhost:6379/0
```

**How It Works:**
1. Extract client IP (handle proxies via X-Forwarded-For)
2. Check Redis sorted set for requests in current window
3. If count >= limit → Return 429 Too Many Requests
4. If under limit → Add request to sorted set, allow through

**Headers Added:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1710518400
Retry-After: 45  (only on 429)
```

**Redis Key Pattern:**
```
rate_limit:{client_ip}
Type: Sorted Set
TTL: 2x window (120 seconds)
```

**Bypass Configuration:**
```bash
RATE_LIMIT_WHITELIST=127.0.0.1,10.0.0.1  # Monitoring, internal
```

---

### 2. XSS Protection (HIGH PRIORITY ✅)

**Implementation:** Pattern-based input sanitization

**Blocked Patterns:**
```python
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script tags
    r'javascript:',                 # JavaScript protocol
    r'on\w+\s*=',                   # Event handlers
    r'<iframe[^>]*>',               # iframes
    r'<object[^>]*>',               # objects
    r'<embed[^>]*>',                # embeds
    r'data:text/html',              # Data URIs
    r'expression\s*\(',             # CSS expressions
]
```

**What Gets Sanitized:**
- Query parameters (`?email=<script>...`)
- JSON body (`{"email": "<script>..."}`)
- Form data (multipart, url-encoded)

**Response on Detection:**
```json
{
  "error": {
    "code": "invalid_input",
    "message": "Invalid characters in request"
  }
}
```

**Logging:**
```
WARNING: XSS attempt detected in query param email
IP: 192.168.1.1, Payload: <script>alert(1)</script>
```

---

### 3. CSRF Protection (MEDIUM PRIORITY ✅)

**Implementation:** Origin validation + optional tokens

**For Public API:**
- Check `Origin` header on POST/PUT/DELETE
- Validate against allowed domains
- Allow API key authentication (bypasses CSRF)

**Allowed Origins:**
```python
allowed_domains = [
    "osfreelance.com",
    "osfreelance.io",
    "freelancerleadtools.osfreelance.com",
    "api.freelancerleadtools.osfreelance.com",
]
```

**For Form Submissions:**
- Double-submit cookie pattern
- Token stored in Redis (24h TTL)
- Validate token on submission

**Exemptions:**
- GET requests (public calculators)
- Health check endpoints
- API documentation

---

### 4. Security Headers (MEDIUM PRIORITY ✅)

**All Responses Include:**

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()
Content-Security-Policy: default-src 'none'; script-src 'self'; ...
Cache-Control: no-store, no-cache, must-revalidate, private
Pragma: no-cache
Expires: 0
```

**Content Security Policy:**
```
default-src 'none'
script-src 'self'
style-src 'self' 'unsafe-inline'
img-src 'self' data: https:
font-src 'self'
connect-src 'self' https://api.osfreelance.com
frame-ancestors 'none'
base-uri 'self'
form-action 'self'
```

---

### 5. Request Size Limits (LOW PRIORITY ✅)

**Configuration:**
```bash
MAX_BODY_SIZE=1048576    # 1 MB
MAX_URL_LENGTH=2048      # 2 KB
```

**Response on Exceed:**
```json
{
  "error": {
    "code": "payload_too_large",
    "message": "Request body exceeds maximum size of 1MB"
  }
}
```

**Status Code:** 413 Payload Too Large

---

### 6. Bot Protection (MEDIUM PRIORITY ✅)

**Implementation:** User-Agent analysis + behavioral detection

**Blocked Patterns:**
```python
BAD_USER_AGENTS = [
    r"bot", r"crawler", r"spider", r"scraper",
    r"curl", r"wget", r"python-requests", r"scrapy",
]
```

**Allowed Bots:**
```python
GOOD_BOTS = [
    "Googlebot", "Bingbot", "Slackbot",
    "Twitterbot", "LinkedInBot",
]
```

**Response on Block:**
```json
{
  "error": {
    "code": "access_denied",
    "message": "Access denied"
  }
}
```

**Logging:**
```
INFO: Blocked bad bot: scraper-bot/1.0
IP: 192.168.1.1
```

---

## Redis Storage Architecture

### Why Redis (Not PostgreSQL)?

| Factor | Redis | PostgreSQL | Decision |
|--------|-------|------------|----------|
| Latency | <1ms | 5-50ms | ✅ Redis |
| Edge Deployment | Single node | Needs DB cluster | ✅ Redis |
| TTL/Eviction | Native | Requires cron | ✅ Redis |
| Cost | Free tier | Always costs | ✅ Redis |
| Scale | Millions ops/sec | Thousands ops/sec | ✅ Redis |

### Lead Storage Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LEAD DATA FLOW                                      │
└─────────────────────────────────────────────────────────────────────────────┘

User Submits Email
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. Check Deduplication (Redis)                                             │
│     Key: lead:emails:{email}                                                │
│     TTL: 24 hours                                                           │
│     If exists → Reject as duplicate                                        │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. Store Lead (Redis Hash)                                                 │
│     Key: lead:{email}:{timestamp}                                           │
│     TTL: 7 days (auto-eviction)                                             │
│     Data: email, source, user_type, country, result, etc.                  │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. Update Analytics (Redis Counters)                                       │
│     lead:count:source:{source} (INCR)                                       │
│     lead:count:date:{date} (INCR)                                           │
│     lead:emails:date:{date} (SADD for unique)                              │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. Queue for CRM Sync (Redis Stream)                                       │
│     Stream: stream:leads                                                    │
│     Data: lead_key, email, source, created_at                              │
│     Worker: Sync to ConvertKit/Mailchimp                                   │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. Auto-Eviction (Redis TTL)                                               │
│     After 7 days → Lead auto-deleted                                       │
│     Already synced to CRM → No data loss                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Redis Key Patterns

| Key Pattern | Type | TTL | Purpose |
|-------------|------|-----|---------|
| `lead:{email}:{timestamp}` | Hash | 7 days | Lead data |
| `lead:emails:{email}` | String | 24 hours | Deduplication |
| `lead:count:source:{source}` | String | 90 days | Analytics |
| `lead:count:date:{date}` | String | 90 days | Daily count |
| `lead:emails:date:{date}` | Set | 90 days | Unique emails |
| `stream:leads` | Stream | N/A | CRM sync queue |
| `rate_limit:{ip}` | Sorted Set | 2 min | Rate limiting |
| `csrf:{session_id}` | String | 24 hours | CSRF tokens |
| `session:{session_id}` | Hash | 24 hours | Session data |

### Data Structure Examples

**Lead Hash:**
```json
{
  "email": "user@example.com",
  "source": "burnout_calculator",
  "user_type": "individual",
  "country": "US",
  "calculator_result": "{...json...}",
  "ip_hash": "a1b2c3d4e5f6...",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2026-03-26T10:00:00Z",
  "synced_to_crm": "false"
}
```

**Analytics Counter:**
```
Key: lead:count:source:burnout_calculator
Value: 1523
TTL: 7776000 (90 days)
```

---

## Threat Model

### Assets Protected

| Asset | Sensitivity | Protection |
|-------|-------------|------------|
| Lead emails | Medium | Rate limiting, deduplication |
| Calculator results | Low | No protection needed |
| IP addresses | Low | Hashed before storage |
| User agents | Low | Logged, not stored |

### Threat Actors

| Actor | Capability | Mitigation |
|-------|------------|------------|
| Spammers | High volume submissions | Rate limiting, deduplication |
| Scrapers | Automated data extraction | Bot protection, rate limiting |
| XSS Attackers | Inject malicious scripts | XSS filtering, CSP |
| CSRF Attackers | Cross-site requests | Origin validation, tokens |

### Attack Vectors & Mitigations

| Attack | Vector | Mitigation | Status |
|--------|--------|------------|--------|
| DoS (Volume) | Flood requests | Rate limiting (100/min) | ✅ |
| DoS (Payload) | Large requests | Size limit (1MB) | ✅ |
| XSS | Inject scripts | Pattern filtering | ✅ |
| CSRF | Cross-site POST | Origin validation | ✅ |
| Scraping | Automated bots | Bot protection | ✅ |
| Spam | Duplicate emails | 24h deduplication | ✅ |
| Injection | SQL/NoSQL | Redis (no SQL), sanitization | ✅ |

---

## Configuration Reference

### Environment Variables

```bash
# Redis (REQUIRED)
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_ENABLED=true
RATE_LIMIT_WHITELIST=127.0.0.1,10.0.0.1

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
BOT_PROTECTION_ENABLED=true
MAX_BODY_SIZE=1048576
MAX_URL_LENGTH=2048

# Lead Storage
LEAD_TTL_SECONDS=604800  # 7 days
LEAD_DEDUPE_TTL_SECONDS=86400  # 24 hours

# CRM Sync
CRM_SYNC_ENABLED=true
CRM_SYNC_BATCH_SIZE=10
```

---

## Monitoring & Alerting

### Metrics to Track

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| Rate limit blocks | Redis counter | > 1000/hour |
| XSS attempts | Application logs | > 100/hour |
| Bot blocks | Application logs | > 500/hour |
| Redis memory | Redis INFO | > 80% maxmemory |
| Redis latency | Redis INFO | > 10ms p99 |
| Lead capture rate | Analytics | Sudden drop > 50% |

### Health Checks

```bash
# Basic health
GET /healthz
Response: {"status": "ok"}

# Redis health
GET /healthz/redis
Response: {"status": "ok", "redis": "connected"}
```

### Logging

**Security Events:**
```
WARNING: XSS attempt detected in query param email
WARNING: CSRF attempt from disallowed origin: evil.com
INFO: Blocked bad bot: scraper-bot/1.0
INFO: Rate limit exceeded for IP: 192.168.1.1
INFO: Duplicate lead suppressed: user@example.com
```

---

## Testing

### Security Test Cases

**Rate Limiting:**
```bash
# Send 100 requests in 60 seconds
for i in {1..100}; do
  curl -X POST https://api.freelancerleadtools.osfreelance.com/leads/capture \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "source": "burnout"}'
done

# 101st request should return 429
```

**XSS Protection:**
```bash
# Test script injection
curl -X POST https://api.freelancerleadtools.osfreelance.com/leads/capture \
  -H "Content-Type: application/json" \
  -d '{"email": "<script>alert(1)</script>@example.com", "source": "burnout"}'

# Should return 400 Bad Request
```

**Bot Protection:**
```bash
# Test with scraper User-Agent
curl -A "scraper-bot/1.0" https://api.freelancerleadtools.osfreelance.com/healthz

# Should return 403 Forbidden
```

---

## Compliance Considerations

### GDPR

| Requirement | Implementation |
|-------------|----------------|
| Data minimization | Only collect email + minimal context |
| Purpose limitation | Only for lead nurturing |
| Storage limitation | 7-day TTL, auto-deletion |
| Right to deletion | Contact support for manual deletion |

### Privacy

| Practice | Implementation |
|----------|----------------|
| IP anonymization | Hash before storage |
| No tracking cookies | Session-only cookies |
| Minimal logging | Security events only |
| No third-party sharing | Only with user consent (CRM) |

---

## Incident Response

### Security Incident Types

| Incident | Severity | Response |
|----------|----------|----------|
| Rate limit bypass | Medium | Investigate, patch |
| XSS bypass | High | Immediate patch, audit |
| CSRF bypass | High | Immediate patch, audit |
| Data breach | Critical | Contain, notify, investigate |

### Response Procedure

1. **Detect** - Monitoring alerts, user reports
2. **Contain** - Block IPs, disable features
3. **Assess** - Determine scope, impact
4. **Remediate** - Fix vulnerability
5. **Notify** - Inform affected users (if required)
6. **Review** - Post-mortem, improve defenses

---

## Appendix: Security Headers Reference

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer |
| `Permissions-Policy` | `geolocation=(), ...` | Restrict features |
| `Content-Security-Policy` | `default-src 'none'; ...` | Restrict resources |
| `Cache-Control` | `no-store, no-cache` | Prevent caching |
| `Pragma` | `no-cache` | Legacy cache control |
| `Expires` | `0` | Expire immediately |

---

**END OF DOCUMENT**

Last reviewed: 2026-03-26  
Next review: 2026-04-26  
Owner: Engineering Team
