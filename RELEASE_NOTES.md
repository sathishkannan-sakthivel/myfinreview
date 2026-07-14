# FinReview Community Edition v1.0.0 Release Notes

FinReview v1.0.0 is the first public Community Edition release candidate. It is positioned as a self-hostable portfolio intelligence application for Indian market portfolios.

Highlights:
- FastAPI backend with SQLModel persistence.
- Vanilla JavaScript frontend with Bootstrap and Chart.js.
- Optional sample portfolio onboarding.
- AI briefing integration through configurable LLM providers.
- All portfolio intelligence capabilities are available in Community Edition.

Known limitations:
- Authentication uses a lightweight signed bearer token and user ownership checks, but is not yet a full JWT/session rotation implementation.
- SQLite is intended for local development; PostgreSQL is recommended for deployment.
- CAS PDF import is disabled in v1.0.0; CSV import and manual entry are the supported import paths.
- Estimated mutual fund overlap is a diagnostic preview and does not yet use live fund look-through holdings.
