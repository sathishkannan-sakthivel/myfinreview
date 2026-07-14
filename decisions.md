# Architecture Decision Records — FinReview Community Edition

These are the key technical decisions made during the design and build of FinReview, recorded as lightweight ADRs (Architecture Decision Records). Each entry captures the context, the options considered, the choice made, and the trade-offs accepted.

---

## ADR-001 — FastAPI over Django or Flask

**Context**  
The backend needed to serve a single-page frontend and expose a clean REST API. Three Python web frameworks were realistic candidates.

**Options considered**

| Framework | Reason considered | Reason not chosen |
|-----------|------------------|-------------------|
| Django | Mature, batteries-included, ORM built in | Too much implicit magic; admin interface and ORM coupling add weight without benefit for an API-only backend |
| Flask | Minimal, flexible | No async support out of the box; manual wiring of validation and serialisation adds boilerplate at scale |
| **FastAPI** | Async-first, automatic OpenAPI docs, Pydantic validation | — |

**Decision**  
FastAPI. The async-first design matches the IO-heavy workload (market data fetches, news ingestion, AI provider calls). Built-in OpenAPI docs at `/docs` reduce the documentation burden significantly. Type-hinted route signatures also make the code self-documenting.

**Trade-offs accepted**  
FastAPI is younger than Django. For a production system with many developers, Django's conventions and ecosystem depth would outweigh the async benefit. For a portfolio project with a small, well-defined scope, FastAPI is the right fit.

---

## ADR-002 — SQLModel with SQLite locally and PostgreSQL in production

**Context**  
The project needed a persistence layer that worked frictionlessly in local development and scaled to a hosted deployment without a schema rewrite.

**Options considered**

| Approach | Trade-off |
|----------|-----------|
| SQLAlchemy directly | More verbose; SQLModel wraps it cleanly for FastAPI/Pydantic integration |
| Django ORM | Tied to Django; rejected with ADR-001 |
| Pure SQLite always | Simple locally; poor concurrency and no managed hosting story |
| PostgreSQL always | Requires a running Postgres instance for local dev; friction for contributors |
| **SQLModel + SQLite local / PostgreSQL hosted** | Clean split: zero-config locally, production-grade hosted |

**Decision**  
SQLModel for the ORM layer (it composes Pydantic models and SQLAlchemy table definitions in one class), SQLite when `DATABASE_URL` is unset (local dev, Docker evaluation), PostgreSQL when `DATABASE_URL` is provided (Render deployment).

**Trade-offs accepted**  
SQLite has limited ALTER TABLE support, which required defensive migration logic in the lifespan startup handler. Any non-trivial schema evolution in production would need Alembic migrations — that is deferred to a future release.

---

## ADR-003 — Separating deterministic analytics from AI-generated insights

**Context**  
Early designs considered passing raw portfolio data directly to an LLM and returning its output as the portfolio summary. This was rejected before the first commit.

**Why separation matters**

- **Correctness**: XIRR, P&L, concentration score, and drift percentage are deterministic calculations. An LLM hallucinating a gain/loss figure is a worse outcome than showing no figure at all.
- **Cost**: Running every portfolio view through an LLM API call would make the app unusable without a paid key.
- **Trust**: Users should be able to verify deterministic outputs. AI outputs carry a clear "informational only" disclaimer precisely because they cannot be verified the same way.
- **Testability**: Unit tests can assert exact XIRR values. They cannot assert that an LLM will produce a specific sentence.

**Decision**  
Two completely separate service layers:

- `portable_analytics_service.py` — deterministic: XIRR via Newton-Raphson, P&L, concentration, drift, tax-loss candidates. Always runs, no API key required.
- `portable_insight_service.py` — AI: OpenRouter call producing briefing text. Degrades gracefully to a static fallback when no key is configured.

The frontend treats these as independent data sources and renders both independently.

**Trade-offs accepted**  
More code to maintain than a single AI endpoint. The separation is worth it: the app is fully functional and correct without any AI key configured.

---

## ADR-004 — OpenRouter over direct OpenAI or Anthropic integration

**Context**  
The AI briefing feature needed an LLM provider. Direct integration with a single provider creates a hard dependency and cost exposure.

**Options considered**

| Option | Trade-off |
|--------|-----------|
| OpenAI API directly | Single provider; cost exposure; harder to swap models |
| Anthropic API directly | Same lock-in risk |
| **OpenRouter** | Single endpoint, multiple provider backends, free-tier models available, model name is a config value |
| Self-hosted model (Ollama) | Zero cost but requires local GPU; not viable for a hosted deployment |

**Decision**  
OpenRouter with the endpoint and model name both externalised as environment variables (`AI_MODEL_ENDPOINT`, `AI_MODEL_NAME`). A compatible self-hosted endpoint (Ollama, LM Studio) can be substituted without touching code. The free-tier default (`google/gemma-3-27b-it:free`) means the feature works out of the box without a paid key, though rate limits apply.

**Trade-offs accepted**  
OpenRouter free-tier models rate-limit aggressively. The insight service handles 429 and 404 responses with a model fallback chain rather than surfacing provider errors to the user.

---

## ADR-005 — Lightweight HMAC bearer token over JWT

**Context**  
The API needed per-user authentication. Full JWT (signed with RS256, refresh token rotation, revocation list) was considered.

**Options considered**

| Option | Trade-off |
|--------|-----------|
| Full JWT (PyJWT / python-jose) | Industry standard; adds a dependency; refresh rotation adds backend state |
| Session cookies | Complicates CORS for a static frontend on a different origin |
| No auth (user_id in request) | Unacceptable; any user could read any other user's data |
| **HMAC signed token (stdlib only)** | No dependency; tamper-evident; expiry enforced; sufficient for a portfolio project |

**Decision**  
`frv1:<user_id>:<utc_timestamp>:<hmac_sha256_signature>` token, issued at login and verified on every protected route. Uses Python stdlib `hmac` and `hashlib` only. 7-day expiry enforced server-side. `hmac.compare_digest` used to prevent timing attacks.

The `AUTH_SECRET_KEY` environment variable is required in hosted deployments. The application logs a warning at startup if the insecure built-in default is still in use.

**Trade-offs accepted**  
No token revocation before expiry (a stolen token is valid for up to 7 days). No refresh token rotation. For a portfolio showcase with no real financial data in production, this is an acceptable trade-off. The README and security notes document the recommended next step: full JWT with rotation.

---

## ADR-006 — Community Edition framing and honest feature scoping

**Context**  
Several features were partially implemented during development: CAS PDF import (service boundary only, no real parser), mutual fund overlap (estimated preview using a hash-based simulation, not live fund look-through data), and password reset (no email infrastructure).

**Options considered**

| Option | Trade-off |
|--------|-----------|
| Ship all features with silent stubs | Misleading; a user uploading their real CAS PDF would see fake imported data |
| Remove stub code entirely | Loses the architectural boundary that a real implementation would slot into |
| **Disable stubs explicitly, document clearly** | HTTP 501 with honest message; frontend controls disabled; README and release notes document limitations |

**Decision**  
CAS upload returns HTTP 501 with a clear message. The frontend input controls are `disabled` with "Disabled in v1.0.0" placeholder text. The overlap diagnostic is labelled "Estimated Diagnostic Preview" in both the UI and documentation, with an explicit note that it does not use live fund look-through data. Forgot-password returns HTTP 501.

The README, RELEASE_NOTES, and DEPLOYMENT docs all state these limitations explicitly.

**Trade-offs accepted**  
The app is less feature-complete than the original design intended. Honest scoping is the correct trade-off: a portfolio project that accurately describes what it does is more credible than one that silently returns fake data.
