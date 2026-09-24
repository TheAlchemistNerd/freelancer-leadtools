# Freelancer LeadTools - Implementation Task List

**Classification:** Internal - Engineering  
**Created:** 2026-03-26  
**Priority:** HIGH (Security & Production Readiness)  
**Owner:** Engineering Team  

---

## Overview

This document outlines all tasks required to implement comprehensive web security and Redis optimization for Freelancer LeadTools.

**Architecture Decision:** LeadTools will use Redis for all data storage (leads, sessions, analytics) instead of PostgreSQL, optimized for edge deployment with automatic TTL-based eviction.

---

## Epic 1: Web Security Implementation

### Task 1.1: Rate Limiting (HIGH PRIORITY)
**Status:** 🟡 In Progress  
**Owner:** Backend Team  
**ETA:** 2026-03-28  

#### Subtasks:
- [x] 1.1.1 Create Redis-backed sliding window rate limiter
  - File: `app/middleware/security.py`
  - Algorithm: Sliding window with Redis sorted sets
  - Default: 100 requests/minute per IP
  - Configurable via env vars
  
- [ ] 1.1.2 Add rate limit headers to responses
  - `X-RateLimit-Limit`: Max requests per window
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Unix timestamp for reset
  - `Retry-After`: Seconds until retry (on 429)

- [ ] 1.1.3 Implement IP extraction with proxy support
  - Check `X-Forwarded-For` header
  - Check `X-Real-IP` header
  - Fall back to `request.client.host`

- [ ] 1.1.4 Add rate limit bypass for whitelisted IPs
  - Environment variable: `RATE_LIMIT_WHITELIST`
  - Use case: Monitoring, internal services

- [ ] 1.1.5 Configure different limits per endpoint
  - `/calculators/*`: 100 req/min (public)
  - `/leads/capture`: 20 req/min (prevent spam)
  - `/healthz`: No limit

- [ ] 1.1.6 Add rate limit metrics
  - Track blocked requests
  - Alert on high block rates
  - Dashboard: Requests per IP, top blockers

#### Acceptance Criteria:
- [ ] Rate limiting functional with Redis
- [ ] Returns 429 with proper headers when exceeded
- [ ] Works behind reverse proxies (Vercel, Cloudflare)
- [ ] Configurable via environment variables
- [ ] Tests cover edge cases (clock skew, Redis failure)

---

### Task 1.2: XSS Protection (HIGH PRIORITY)
**Status:** 🟡 In Progress  
**Owner:** Backend Team  
**ETA:** 2026-03-28  

#### Subtasks:
- [x] 1.2.1 Create XSS pattern detection middleware
  - File: `app/middleware/security.py`
  - Patterns: `<script>`, `javascript:`, `on*=` handlers, `<iframe>`, etc.
  - Regex compilation for performance

- [ ] 1.2.2 Sanitize query parameters
  - Check all query params for XSS patterns
  - Return 400 Bad Request on detection
  - Log attempt with IP and payload

- [ ] 1.2.3 Sanitize JSON request bodies
  - Parse JSON before Pydantic validation
  - Recursively check all string values
  - Handle nested objects and arrays

- [ ] 1.2.4 Sanitize form data
  - Check `application/x-www-form-urlencoded`
  - Check `multipart/form-data`

- [ ] 1.2.5 Add output encoding for responses
  - Set `Content-Type: application/json`
  - Escape HTML in error messages
  - Never reflect user input without encoding

- [ ] 1.2.6 Create XSS test suite
  - Test common XSS payloads
  - Test bypass attempts
  - Test false positives (legitimate input)

#### Acceptance Criteria:
- [ ] Blocks common XSS payloads
- [ ] Returns 400 with generic error (don't reveal detection)
- [ ] Logs attempts for security monitoring
- [ ] No false positives on legitimate input
- [ ] Performance impact < 5ms per request

---

### Task 1.3: CSRF Protection (MEDIUM PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Backend Team  
**ETA:** 2026-03-30  

#### Subtasks:
- [ ] 1.3.1 Implement Origin/Referer header validation
  - Check `Origin` header on POST/PUT/DELETE
  - Validate against allowed domains
  - Allow list: `osfreelance.com`, `osfreelance.io`

- [ ] 1.3.2 Add CSRF token for form submissions
  - Generate token on page load
  - Store in session (Redis)
  - Validate on form submission

- [ ] 1.3.3 Implement double-submit cookie pattern
  - Send CSRF token in cookie
  - Require same token in header
  - Compare on server

- [ ] 1.3.4 Exempt public calculator endpoints
  - GET `/calculators/*`: No CSRF needed
  - POST `/leads/capture`: CSRF required (or API key)

- [ ] 1.3.5 Add API key authentication for services
  - Header: `X-API-Key`
  - Bypasses CSRF check
  - For service-to-service communication

#### Acceptance Criteria:
- [ ] Blocks cross-site POST requests
- [ ] Allows same-origin requests
- [ ] API key authentication works
- [ ] CSRF tokens expire after 24 hours
- [ ] No impact on legitimate API consumers

---

### Task 1.4: Security Headers (MEDIUM PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Backend Team  
**ETA:** 2026-03-29  

#### Subtasks:
- [ ] 1.4.1 Add `X-Content-Type-Options: nosniff`
  - Prevents MIME type sniffing
  
- [ ] 1.4.2 Add `X-Frame-Options: DENY`
  - Prevents clickjacking
  
- [ ] 1.4.3 Add `X-XSS-Protection: 1; mode=block`
  - Legacy but still useful
  
- [ ] 1.4.4 Add `Referrer-Policy: strict-origin-when-cross-origin`
  - Controls referrer information
  
- [ ] 1.4.5 Add `Permissions-Policy`
  - Disable: geolocation, microphone, camera, payment, etc.
  
- [ ] 1.4.6 Add `Content-Security-Policy`
  - `default-src 'none'`
  - `script-src 'self'`
  - `frame-ancestors 'none'`
  
- [ ] 1.4.7 Add cache control for API responses
  - `Cache-Control: no-store, no-cache`
  - `Pragma: no-cache`
  - `Expires: 0`

#### Acceptance Criteria:
- [ ] All security headers present on every response
- [ ] CSP doesn't break legitimate functionality
- [ ] Headers verified with security scanner
- [ ] No console errors from CSP

---

### Task 1.5: Request Size Limits (LOW PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Backend Team  
**ETA:** 2026-03-30  

#### Subtasks:
- [ ] 1.5.1 Set maximum body size (1 MB for leadtools)
  - Prevents DoS via large payloads
  - Check `Content-Length` header
  
- [ ] 1.5.2 Return 413 Payload Too Large
  - Clear error message
  - Include max size in response
  
- [ ] 1.5.3 Limit URL length
  - Max 2048 characters
  - Prevents buffer overflow attacks

#### Acceptance Criteria:
- [ ] Rejects requests > 1 MB
- [ ] Returns proper 413 status
- [ ] No impact on legitimate requests

---

### Task 1.6: Bot Protection (MEDIUM PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Backend Team  
**ETA:** 2026-03-30  

#### Subtasks:
- [ ] 1.6.1 User-Agent analysis
  - Block known bad bots (scrapers, scrapers)
  - Allow good bots (Googlebot, Bingbot)
  - Log requests without User-Agent

- [ ] 1.6.2 Implement basic behavioral analysis
  - Track request frequency per IP
  - Detect automated patterns
  - Flag suspicious activity

- [ ] 1.6.3 Add honeypot fields for forms
  - Hidden field in lead capture form
  - If filled, reject as bot
  - Invisible to humans

- [ ] 1.6.4 Implement IP-based blocking
  - Block IPs with high bot scores
  - TTL: 24 hours
  - Store in Redis

- [ ] 1.6.5 Add CAPTCHA for suspicious requests
  - Only trigger on suspicious patterns
  - Use hCaptcha (privacy-friendly)
  - Skip for normal users

#### Acceptance Criteria:
- [ ] Blocks common scrapers and bots
- [ ] Allows search engine bots
- [ ] Honeypot catches basic bots
- [ ] No impact on legitimate users
- [ ] Bot attempts logged for analysis

---

### Task 1.7: Input Validation Enhancement (MEDIUM PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Backend Team  
**ETA:** 2026-03-29  

#### Subtasks:
- [ ] 1.7.1 Enhance email validation
  - Pydantic `EmailStr` already in use
  - Add MX record verification (async)
  - Block disposable email domains

- [ ] 1.7.2 Add phone number validation (for SMS leads)
  - Format: E.164
  - Country code validation
  - Carrier lookup (optional)

- [ ] 1.7.3 Sanitize country codes
  - Validate against ISO 3166-1 alpha-2
  - Prevent injection via country field

- [ ] 1.7.4 Add request fingerprinting
  - Hash of: IP + User-Agent + Accept-Language
  - Detect duplicate submissions
  - Prevent lead spam

#### Acceptance Criteria:
- [ ] Invalid emails rejected
- [ ] Disposable emails flagged
- [ ] Country codes validated
- [ ] Duplicate submissions detected

---

## Epic 2: Redis Storage Implementation

### Task 2.1: Redis Lead Storage (HIGH PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Backend Team  
**ETA:** 2026-03-29  

#### Subtasks:
- [ ] 2.1.1 Create Redis repository for leads
  - File: `app/repositories/lead_repository.py`
  - Key pattern: `lead:{email}:{timestamp}`
  - Data structure: Redis Hash
  
- [ ] 2.1.2 Implement TTL-based eviction
  - TTL: 7 days (configurable)
  - Auto-delete after TTL
  - Sync to CRM before deletion
  
- [ ] 2.1.3 Store lead data structure
  ```python
  {
    "email": "user@example.com",
    "source": "burnout_calculator",
    "user_type": "individual",
    "country": "US",
    "calculator_result": "{...json...}",
    "ip_hash": "sha256(...)",
    "user_agent": "Mozilla/5.0...",
    "created_at": "2026-03-26T10:00:00Z",
    "synced_to_crm": "false"
  }
  ```

- [ ] 2.1.4 Implement lead deduplication
  - Check if email exists in last 24 hours
  - Update existing lead instead of duplicate
  - Track submission count

- [ ] 2.1.5 Add CRM sync worker
  - Background job (Redis Stream)
  - Sync leads to ConvertKit/Mailchimp
  - Mark as synced in Redis
  - Retry on failure

- [ ] 2.1.6 Implement lead analytics in Redis
  - Counter: `leads:count:{source}`
  - Counter: `leads:count:{date}`
  - Set: `leads:emails:{date}` (for unique count)

#### Acceptance Criteria:
- [ ] Leads stored in Redis with TTL
- [ ] Auto-eviction after 7 days
- [ ] CRM sync working (ConvertKit/Mailchimp)
- [ ] Deduplication prevents spam
- [ ] Analytics counters accurate
- [ ] Tests cover Redis failure scenarios

---

### Task 2.2: Redis Session Management (MEDIUM PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Backend Team  
**ETA:** 2026-03-30  

#### Subtasks:
- [ ] 2.2.1 Create session storage for calculators
  - Key pattern: `session:{session_id}`
  - TTL: 24 hours
  - Store calculator state

- [ ] 2.2.2 Implement session-based calculator state
  - Multi-step calculators
  - Save progress between steps
  - Resume abandoned sessions

- [ ] 2.2.3 Add CSRF token storage
  - Key pattern: `csrf:{session_id}`
  - TTL: 24 hours
  - Validate on form submission

- [ ] 2.2.4 Implement session cleanup
  - Expired sessions auto-delete (Redis TTL)
  - Manual cleanup for orphaned sessions
  - Track active session count

#### Acceptance Criteria:
- [ ] Sessions stored in Redis
- [ ] Auto-expire after 24 hours
- [ ] CSRF tokens validated
- [ ] Multi-step calculators work
- [ ] No memory leaks

---

### Task 2.3: Redis Analytics (MEDIUM PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Backend Team  
**ETA:** 2026-03-30  

#### Subtasks:
- [ ] 2.3.1 Implement real-time counters
  - `analytics:calculators:{name}:views`
  - `analytics:calculators:{name}:completions`
  - `analytics:leads:captured`
  - Increment with `INCR`

- [ ] 2.3.2 Create time-series data
  - Key pattern: `analytics:leads:{YYYY-MM-DD}`
  - Store daily lead counts
  - TTL: 90 days (roll up to monthly after)

- [ ] 2.3.3 Track conversion funnels
  - Step 1: Calculator started
  - Step 2: Results shown
  - Step 3: Email entered
  - Step 4: Lead captured
  - Store in Redis Hash

- [ ] 2.3.4 Implement geographic analytics
  - Key pattern: `analytics:leads:country:{country_code}`
  - Track leads by country
  - PPP pricing optimization

- [ ] 2.3.5 Create analytics API endpoint
  - `GET /analytics/summary`
  - Returns: views, completions, conversion rate
  - Cache results (5 min TTL)

#### Acceptance Criteria:
- [ ] Real-time counters accurate
- [ ] Time-series data stored
- [ ] Funnel tracking works
- [ ] Geographic data collected
- [ ] Analytics API responsive (< 100ms)

---

### Task 2.4: Redis Configuration & Operations (HIGH PRIORITY)
**Status:** ⏳ Pending  
**Owner:** DevOps Team  
**ETA:** 2026-03-28  

#### Subtasks:
- [ ] 2.4.1 Configure Redis connection pooling
  - Max connections: 50
  - Timeout: 5 seconds
  - Retry: 3 attempts

- [ ] 2.4.2 Set up Redis persistence (AOF)
  - Append-only file for durability
  - Sync: Every second
  - Prevents data loss on restart

- [ ] 2.4.3 Configure Redis memory limits
  - Max memory: 512 MB (Vercel/edge)
  - Eviction policy: `allkeys-lru`
  - Monitor memory usage

- [ ] 2.4.4 Implement Redis health checks
  - Endpoint: `/healthz/redis`
  - Check: Connection, latency, memory
  - Alert on failures

- [ ] 2.4.5 Set up Redis monitoring
  - Metrics: Connections, memory, ops/sec
  - Alerts: High memory, slow queries
  - Dashboard: RedisInsight or Grafana

- [ ] 2.4.6 Configure Redis for edge deployment
  - Vercel: Use Upstash (serverless Redis)
  - Alternative: Redis Cloud
  - Fallback: In-memory (development only)

#### Acceptance Criteria:
- [ ] Connection pooling configured
- [ ] AOF persistence enabled
- [ ] Memory limits set
- [ ] Health checks passing
- [ ] Monitoring dashboard created
- [ ] Edge deployment tested (Vercel + Upstash)

---

## Epic 3: Testing & Quality Assurance

### Task 3.1: Security Testing (HIGH PRIORITY)
**Status:** ⏳ Pending  
**Owner:** QA Team  
**ETA:** 2026-04-01  

#### Subtasks:
- [ ] 3.1.1 Penetration testing
  - OWASP Top 10 coverage
  - Automated: OWASP ZAP
  - Manual: Security review

- [ ] 3.1.2 Rate limit testing
  - Test with multiple IPs
  - Test proxy bypass attempts
  - Test Redis failure scenarios

- [ ] 3.1.3 XSS payload testing
  - Use XSS payload lists (OWASP, PortSwigger)
  - Test bypass attempts
  - Verify logging

- [ ] 3.1.4 CSRF testing
  - Test cross-site POST
  - Test token validation
  - Test origin validation

- [ ] 3.1.5 Bot protection testing
  - Test with common bot User-Agents
  - Test honeypot fields
  - Verify good bots allowed

#### Acceptance Criteria:
- [ ] No critical vulnerabilities found
- [ ] Rate limiting effective
- [ ] XSS payloads blocked
- [ ] CSRF attacks prevented
- [ ] Bots detected and blocked

---

### Task 3.2: Load Testing (MEDIUM PRIORITY)
**Status:** ⏳ Pending  
**Owner:** QA Team  
**ETA:** 2026-04-02  

#### Subtasks:
- [ ] 3.2.1 Baseline performance testing
  - 100 concurrent users
  - Measure: Latency, throughput, error rate
  - Establish baseline

- [ ] 3.2.2 Stress testing
  - 1000 concurrent users
  - Find breaking point
  - Identify bottlenecks

- [ ] 3.2.3 Redis performance testing
  - Measure: Read/write latency
  - Test: Connection pool exhaustion
  - Verify: TTL eviction

- [ ] 3.2.4 Edge deployment testing
  - Deploy to Vercel
  - Test with Upstash Redis
  - Measure: Cold start, latency

#### Acceptance Criteria:
- [ ] p95 latency < 500ms at 100 users
- [ ] No errors at 100 users
- [ ] Graceful degradation at 1000 users
- [ ] Redis latency < 10ms
- [ ] Edge deployment functional

---

### Task 3.3: Integration Testing (MEDIUM PRIORITY)
**Status:** ⏳ Pending  
**Owner:** QA Team  
**ETA:** 2026-04-01  

#### Subtasks:
- [ ] 3.3.1 CRM integration testing
  - Test ConvertKit sync
  - Test Mailchimp sync
  - Verify: Data mapping, error handling

- [ ] 3.3.2 Email delivery testing
  - Send test emails
  - Verify: Delivery, formatting, links
  - Test: Unsubscribe flow

- [ ] 3.3.3 Analytics integration testing
  - Verify: Counters accurate
  - Test: Time-series data
  - Validate: Funnel tracking

#### Acceptance Criteria:
- [ ] CRM sync working end-to-end
- [ ] Emails delivered successfully
- [ ] Analytics data accurate
- [ ] Error handling graceful

---

## Epic 4: Documentation & Runbooks

### Task 4.1: Security Documentation (MEDIUM PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Engineering Team  
**ETA:** 2026-04-03  

#### Subtasks:
- [ ] 4.1.1 Document security architecture
  - File: `docs/internal/SECURITY_ARCHITECTURE.md`
  - Include: All middleware, configurations
  - Diagram: Request flow with security checks

- [ ] 4.1.2 Create security runbook
  - File: `docs/internal/SECURITY_RUNBOOK.md`
  - Include: Incident response, common attacks
  - Contact: Security team escalation

- [ ] 4.1.3 Document Redis architecture
  - File: `docs/internal/REDIS_ARCHITECTURE.md`
  - Include: Key patterns, TTLs, eviction
  - Diagram: Data flow

#### Acceptance Criteria:
- [ ] Security architecture documented
- [ ] Runbook complete with procedures
- [ ] Redis architecture clear
- [ ] Team trained on procedures

---

### Task 4.2: API Documentation (LOW PRIORITY)
**Status:** ⏳ Pending  
**Owner:** Engineering Team  
**ETA:** 2026-04-05  

#### Subtasks:
- [ ] 4.2.1 Update OpenAPI spec
  - Add: Security requirements
  - Add: Rate limit info
  - Add: Error responses

- [ ] 4.2.2 Document rate limiting
  - Public docs: Rate limits per endpoint
  - Headers explained
  - Retry guidance

- [ ] 4.2.3 Document authentication
  - API key usage
  - CSRF token flow
  - Examples for each

#### Acceptance Criteria:
- [ ] OpenAPI spec complete
- [ ] Rate limits documented
- [ ] Authentication clear
- [ ] Examples working

---

## Summary & Timeline

| Epic | Tasks | Priority | ETA |
|------|-------|----------|-----|
| 1. Web Security | 7 tasks | HIGH | 2026-03-30 |
| 2. Redis Storage | 4 tasks | HIGH | 2026-03-30 |
| 3. Testing & QA | 3 tasks | MEDIUM | 2026-04-02 |
| 4. Documentation | 2 tasks | LOW | 2026-04-05 |

### Critical Path:
1. **Task 1.1** - Rate Limiting (blocks production deployment)
2. **Task 2.1** - Redis Lead Storage (blocks production deployment)
3. **Task 2.4** - Redis Configuration (blocks all Redis tasks)
4. **Task 3.1** - Security Testing (required before production)

### Production Readiness Gate:
- [ ] All HIGH priority tasks complete
- [ ] Security testing passed
- [ ] Load testing passed
- [ ] Redis persistence configured
- [ ] Monitoring in place
- [ ] Runbooks documented

---

**Last Updated:** 2026-03-26  
**Next Review:** 2026-03-28  
**Project Lead:** Engineering Team
> Historical backlog: superseded by the root repository's
> docs/internal/leadtools-execution-plan.md. Do not implement Redis-only durable
> lead storage or calculator sessions from this old list. PostgreSQL owns leads.
