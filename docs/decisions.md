# Architecture Decision Records — FinReview Community Edition

Lightweight ADRs covering every significant technical decision across the full project lifecycle.
Each entry records the context, options considered, the decision made, and the trade-offs accepted.

| ADR | Area | Status |
|-----|------|--------|
| [ADR-001](#adr-001--fastapi-over-django-or-flask) | Web framework | Accepted |
| [ADR-002](#adr-002--sqlmodel-with-sqlite-locally-and-postgresql-in-production) | Persistence layer | Accepted |
| [ADR-003](#adr-003--static-frontend-over-a-javascript-framework) | Frontend architecture | Accepted |
| [ADR-004](#adr-004--separating-deterministic-analytics-from-ai-generated-insights) | Analytics vs AI separation | Accepted |
| [ADR-005](#adr-005--openrouter-over-direct-openai-or-anthropic-integration) | AI provider | Accepted |
| [ADR-006](#adr-006--lightweight-hmac-bearer-token-over-jwt) | Authentication | Accepted |
| [ADR-007](#adr-007--community-edition-framing-and-honest-feature-scoping) | Feature scoping | Accepted |
| [ADR-008](#adr-008--layered-service-architecture-over-route-level-logic) | Backend structure | Accepted |
| [ADR-009](#adr-009--yahoo-finance--mfapiinmix-for-market-data) | Market data | Accepted |
| [ADR-010](#adr-010--xirr-via-newton-raphson-without-a-financial-library) | XIRR implementation | Accepted |
| [ADR-011](#adr-011--docker-support-alongside-render-deployment) | Deployment strategy | Accepted |
| [ADR-012](#adr-012--admin-shutdown-endpoint-gated-behind-auth) | Operational tooling | Accepted |

---

## ADR-001 — FastAPI over Django or Flask

**Context**
The backend needed to serve a single-page frontend and expose a clean REST API. Three Python web frameworks were realistic candidates.

**Options considered**

| Framework | Reason considered | Reason not chosen |
|-----------|------------------|-------------------|
| Django | Mature, batteries-included, ORM built in | Too much implicit magic; admin and ORM coupling add weight without benefit for an API-only backend |
| Flask | Minimal, flexible | No async support out of the box; manual wiring of validation and serialisation adds boilerplate at scale |
| **FastAPI** | Async-first, automatic OpenAPI docs, Pydantic validation | — |

**Decision**
FastAPI. The async-first design matches the IO-heavy workload (market data fetches, news ingestion, AI provider calls). Built-in OpenAPI docs at `/docs` reduce the documentation burden significantly. Type-hinted route signatures make the code self-documenting and the request/response contract explicit without a separate schema layer.

**Trade-offs accepted**
FastAPI is younger than Django. For a production system with many developers, Django's conventions and ecosystem depth would outweigh the async benefit. For a focused, well-scoped project, FastAPI is the right fit.

---

## ADR-002 — SQLModel with SQLite locally and PostgreSQL in production

**Context**
The project needed a persistence layer that worked frictionlessly in local development and could scale to a hosted deployment without a schema rewrite or environment-specific code branches.

**Options considered**

| Approach | Trade-off |
|----------|-----------|
| SQLAlchemy directly | More verbose; SQLModel wraps it cleanly for FastAPI/Pydantic integration |
| Django ORM | Tied to Django; rejected with ADR-001 |
| Pure SQLite always | Simple locally; poor write concurrency under load, no managed hosting story |
| PostgreSQL always | Requires a running Postgres instance for local dev; friction for first-run setup |
| **SQLModel + SQLite local / PostgreSQL hosted** | Zero-config locally, production-grade hosted, same model classes throughout |

**Decision**
SQLModel for the ORM layer — it composes Pydantic models and SQLAlchemy table definitions in one class, which fits naturally with FastAPI's Pydantic-first design. SQLite is used when `DATABASE_URL` is unset (local dev, Docker evaluation). PostgreSQL is used when `DATABASE_URL` is provided (Render deployment). The application detects this automatically at startup with no code changes required.

**Trade-offs accepted**
SQLite has limited ALTER TABLE support, which required defensive migration logic in the lifespan startup handler. Any non-trivial schema evolution in production requires Alembic migrations — deferred to a future release. The SQLModel project itself is still maturing; for a large production codebase, raw SQLAlchemy with Alembic from day one would be safer.

---

## ADR-003 — Static Frontend over a JavaScript Framework

**Context**
The UI needed to be simple to deploy, maintainable without a build pipeline, and accessible to backend engineers reviewing the project without requiring Node.js expertise.

**Options considered**

| Approach | Trade-off |
|----------|-----------|
| React / Next.js | Component model is powerful; adds build step, Node dependency, and bundle complexity |
| Vue.js | Lighter than React; still requires build tooling for production |
| Angular | Enterprise-grade but heavy for a portfolio project with a single developer |
| **Vanilla HTML + Bootstrap 5 + Chart.js** | No build step, no Node dependency, deployable as static files to any host |

**Decision**
Static HTML, Bootstrap 5 for layout and components, Chart.js for data visualisation, and plain JavaScript for interactivity. The entire frontend is a folder of static files served by any web host. This matches the "Backend-First Architecture" principle — the backend carries all business logic and the frontend is purely presentational.

**Trade-offs accepted**
No component model means more manual DOM management as the UI grows. State management is manual rather than reactive. These trade-offs are acceptable for a single-developer project at this scope. A production version with a larger team would benefit from a proper component framework.

---

## ADR-004 — Separating Deterministic Analytics from AI-Generated Insights

**Context**
Early designs considered passing raw portfolio data directly to an LLM and returning its output as the portfolio analytics summary. This was rejected before the first commit.

**Why separation matters**
- **Correctness**: XIRR, P&L, concentration score, and drift percentage are deterministic calculations. An LLM hallucinating a gain/loss figure is a worse outcome than showing no figure at all.
- **Cost**: Running every portfolio view through an LLM API call makes the app unusable without a paid key and introduces unpredictable latency.
- **Trust**: Users can verify deterministic outputs. AI outputs carry a clear "informational only" disclaimer precisely because they cannot be verified the same way.
- **Testability**: Unit tests can assert exact XIRR values. They cannot assert that an LLM produces a specific sentence.
- **Availability**: Analytics work offline and without any API key. AI briefings degrade gracefully to a fallback when no key is configured.

**Decision**
Two completely separate service layers:
- `portable_analytics_service.py` — deterministic: XIRR, P&L, concentration, drift, tax-loss candidates. Always runs, no API key required.
- `portable_insight_service.py` — AI: OpenRouter call producing briefing text. Degrades gracefully to a static fallback when no key is configured.

The frontend treats these as independent data sources and renders them independently. The API responses are separate endpoints, not a combined payload.

**Trade-offs accepted**
More service code to maintain than a single AI endpoint. The separation is worth it: the app is fully functional and analytically correct without any AI key configured.

---

## ADR-005 — OpenRouter over Direct OpenAI or Anthropic Integration

**Context**
The AI briefing feature needed an LLM provider. Direct integration with a single provider creates a hard dependency and cost exposure.

**Options considered**

| Option | Trade-off |
|--------|-----------|
| OpenAI API directly | Single provider; cost exposure; harder to swap models without code changes |
| Anthropic API directly | Same provider lock-in risk |
| **OpenRouter** | Single endpoint, multiple provider backends, free-tier models available, model name is a config value |
| Self-hosted model (Ollama) | Zero API cost but requires local GPU; not viable for a hosted deployment |

**Decision**
OpenRouter with both the endpoint and model name externalised as environment variables (`AI_MODEL_ENDPOINT`, `AI_MODEL_NAME`). A compatible self-hosted endpoint (Ollama, LM Studio) can be substituted without touching code. The free-tier default (`google/gemma-3-27b-it:free`) means the AI feature works out of the box without a paid key, though rate limits apply. The insight service implements a model fallback chain — if the primary model returns 429 or 404, it retries with an alternative model before falling back to a static response.

**Trade-offs accepted**
OpenRouter free-tier models rate-limit aggressively. The fallback chain mitigates this but does not eliminate it. A production deployment with real users would require a paid API key.

---

## ADR-006 — Lightweight HMAC Bearer Token over JWT

**Context**
The API needed per-user authentication. Full JWT with RS256 signing, refresh token rotation, and a revocation list was considered alongside simpler alternatives.

**Options considered**

| Option | Trade-off |
|--------|-----------|
| Full JWT (PyJWT / python-jose) | Industry standard; adds a dependency; refresh rotation adds backend state and complexity |
| Session cookies | Complicates CORS for a static frontend served from a different origin than the API |
| No auth (user_id in request body) | Unacceptable; any user could read or modify any other user's data |
| **HMAC signed token (stdlib only)** | No extra dependency; tamper-evident; expiry enforced server-side; sufficient for this scope |

**Decision**
`frv1:<user_id>:<utc_timestamp>:<hmac_sha256_signature>` token format, issued at login and verified on every protected route. Uses Python stdlib `hmac` and `hashlib` only — no additional dependency. 7-day expiry enforced server-side. `hmac.compare_digest` used to prevent timing attacks on signature comparison. `AUTH_SECRET_KEY` is required in hosted deployments; the application logs a startup warning if the insecure built-in default is still in use.

**Trade-offs accepted**
No token revocation before expiry — a stolen token remains valid for up to 7 days. No refresh token rotation. For a portfolio showcase with no real financial data in production, this is an acceptable trade-off. The SECURITY.md documents the recommended next step for a production system: full JWT with refresh rotation and a revocation store.

---

## ADR-007 — Community Edition Framing and Honest Feature Scoping

**Context**
Several features were partially implemented during development: CAS PDF import (service boundary defined, no real parser), mutual fund overlap (estimated preview using a hash-based simulation, not live fund look-through data), and password reset (no email infrastructure). The question was how to handle these incomplete features at release.

**Options considered**

| Option | Trade-off |
|--------|-----------|
| Ship all features with silent stubs | Misleading — a user uploading a real CAS PDF would see fake imported data with no indication it was fabricated |
| Remove stub code entirely | Loses the architectural service boundary that a real implementation would slot into |
| **Disable stubs explicitly, document clearly** | HTTP 501 with honest message; frontend controls disabled; README, RELEASE_NOTES, and DEPLOYMENT docs state limitations clearly |

**Decision**
CAS upload returns HTTP 501 with an explicit message. Frontend input controls carry `disabled` attributes and "Disabled in v1.0.0" placeholder text. The overlap diagnostic is labelled "Estimated Diagnostic Preview" in both the UI and documentation, with an explicit note that it does not use live fund look-through data. Forgot-password returns HTTP 501. Every limitation is documented in README, RELEASE_NOTES, and DEPLOYMENT.

This decision was reached after an external architecture review identified the original stub behaviour as misleading — the most significant quality gate in the project's development cycle.

**Trade-offs accepted**
The released application is less feature-complete than the original design intended. Honest scoping is the correct trade-off: a portfolio project that accurately describes what it does is more credible than one that silently returns fabricated data.

---

## ADR-008 — Layered Service Architecture over Route-Level Logic

**Context**
As the feature set grew, a choice emerged between placing business logic directly inside FastAPI route handlers (common in smaller projects) or separating it into dedicated service classes.

**Options considered**

| Approach | Trade-off |
|----------|-----------|
| Logic in route handlers | Simpler for small apps; becomes untestable and unmaintainable as logic grows |
| **Dedicated service layer** | More files and abstraction; logic is independently testable and reusable across routes |

**Decision**
Business logic is entirely contained in the `services/`, `analytics/`, `alerts/`, `ai/`, and `news/` modules. Route handlers in `main.py` are responsible only for request parsing, calling the appropriate service, and returning the response. This means any service can be unit-tested independently of the HTTP layer, and any future route (CLI, WebSocket, scheduled task) can call the same service without duplicating logic.

**Trade-offs accepted**
More files and indirection than a simple single-file FastAPI app. For a project of this scale with a single developer, the added structure is deliberate — it demonstrates architectural discipline rather than just getting something working.

---

## ADR-009 — Yahoo Finance + mfapi.in Mix for Market Data

**Context**
The application needed live prices for both Indian equities (NSE/BSE listed) and Indian mutual funds. No single free API covers both cleanly.

**Options considered**

| Source | Coverage | Limitation |
|--------|----------|------------|
| NSE official API | Indian equities | Unofficial, frequently changes, no SDK |
| Alpha Vantage | Global equities | Rate-limited; mutual funds not covered |
| **Yahoo Finance** | Indian equities via `.NS` / `.BO` suffixes | Free; rate-limited; no official support |
| **mfapi.in** | Indian mutual fund NAVs | Free; Indian MFs only; no equities |

**Decision**
A provider abstraction layer (`portable_price_service.py`) selects the correct provider based on the asset symbol. Indian equity symbols use Yahoo Finance (`.NS` suffix for NSE). Mutual fund symbols use mfapi.in. The abstraction means either provider can be swapped or supplemented without changes to the analytics or portfolio service layers.

**Trade-offs accepted**
Both providers are unofficial or community-maintained with no SLA. Price data may be delayed or unavailable during outages. For a portfolio showcase this is acceptable; a production system would require a paid, contractual data feed.

---

## ADR-010 — XIRR via Newton-Raphson Without a Financial Library

**Context**
XIRR (Extended Internal Rate of Return) is the primary return metric for SIP-style investments with irregular cashflow dates. Standard Python financial libraries either require heavy dependencies or do not handle the irregular-date case correctly for Indian mutual fund investment patterns.

**Options considered**

| Approach | Trade-off |
|----------|-----------|
| numpy-financial `irr()` | Regular periods only; does not support arbitrary dates |
| scipy `brentq` solver | Works but adds scipy as a dependency for one function |
| **Custom Newton-Raphson** | No extra dependency; full control over convergence and edge-case handling; educational |

**Decision**
A custom Newton-Raphson implementation in `analytics/xirr.py`. The function takes a list of `(date, cashflow)` tuples with no assumption about period regularity. Convergence tolerance and max iteration count are explicit constants. Edge cases (all-positive cashflows, single transaction, zero total) return `None` rather than raising, allowing the UI to display `—` gracefully.

**Trade-offs accepted**
A custom numerical solver requires careful handling of convergence failures and pathological inputs. The implementation is thoroughly commented and covers the known edge cases, but a financial library with a maintained test suite would be more robust in production.

---

## ADR-011 — Docker Support Alongside Render Deployment

**Context**
The primary deployment target is Render (backend) with static file hosting (frontend). The question was whether to also support Docker, and if so, how to structure it.

**Options considered**

| Approach | Trade-off |
|----------|-----------|
| Render only, no Docker | Simplest; ties the project to one platform |
| Docker only | Portable but heavier setup; less beginner-friendly for contributors |
| **Both: Render + Docker** | Render for hosted deployment; Docker for local evaluation and self-hosting |

**Decision**
A `Dockerfile` and `docker-compose.yml` are provided for local evaluation and self-hosting. The `render.yaml` defines the Render-specific deployment. Both use the same environment variable names from `.env.example` so configuration is consistent. The `docker-compose.yml` starts both the backend and a simple static file server for the frontend, making the full application runnable in one command locally.

**Trade-offs accepted**
Two deployment paths to maintain. The Docker configuration is deliberately kept simple (no multi-stage build, no Kubernetes manifests) to remain approachable for a portfolio project.

---

## ADR-012 — Admin Shutdown Endpoint Gated Behind Auth

**Context**
A `/admin/shutdown` endpoint was added to enable clean programmatic shutdown on Windows during local development (where Ctrl+C in uvicorn is sometimes unreliable). The original implementation had no authentication.

**Problem identified**
An external architecture review identified that an unauthenticated shutdown endpoint, if present in a hosted deployment, could be triggered anonymously to kill the production process. The endpoint was never intended for production use but was not guarded against it.

**Options considered**

| Option | Trade-off |
|--------|-----------|
| Remove the endpoint entirely | Solves the security issue; removes a useful local dev tool |
| IP whitelist | Fragile; doesn't work behind Render's proxy |
| **Bearer token check matching AUTH_SECRET_KEY** | Simple; consistent with existing auth approach; anonymous requests get 401 |

**Decision**
The endpoint now requires `Authorization: Bearer <AUTH_SECRET_KEY>` — the raw secret value, not a user token. This means it cannot be triggered without knowing the deployment secret. In local development where `AUTH_SECRET_KEY` is the default value, the endpoint remains easy to call. In production, it requires the operator's secret, making accidental or malicious triggering effectively impossible.

**Trade-offs accepted**
Using the raw secret value as the bearer credential is unconventional — it does not go through the normal `_verify_token` flow. This is intentional: the endpoint is an operational tool, not a user-facing API, and tying it to a specific user's token would add unnecessary complexity for no benefit.
