# API Reference

FastAPI exposes interactive OpenAPI documentation at `/docs` when the backend is running.

## Auth

- `POST /auth/signup`: Create a user.
- `POST /auth/login`: Authenticate a user.
- `GET /auth/profile/{user_id}`: Read profile settings.
- `POST /auth/profile`: Update profile settings.
- `POST /auth/target-allocation`: Save target allocation and drift sensitivity.

## Portfolio

- `GET /portfolio/{user_id}/summary`: Portfolio valuation, cost, P&L, holdings, and profile metadata.
- `GET /portfolio/{user_id}`: Raw holdings.
- `POST /portfolio/transaction`: Record one transaction.
- `POST /portfolio/bulk-transaction`: Record multiple transactions.
- `POST /portfolio/upload-cas`: CAS import service endpoint.
- `POST /sample-portfolio/{user_id}`: Load optional sample transactions for an empty account.

## Analytics and Intelligence

- `GET /analytics/{user_id}`: Latest analytics summary.
- `POST /analytics/{user_id}/calculate`: Recalculate analytics and alerts.
- `GET /analytics/overlap/{user_id}`: Mutual fund stock overlap diagnostics.
- `GET /insights/{user_id}`: Stored AI insights.
- `POST /insights/{user_id}/generate`: Generate AI insights.
- `GET /market/context`: Nifty market context.

## Alerts and News

- `POST /alerts/rule`: Create an alert rule.
- `GET /alerts/{user_id}/rules`: List alert rules.
- `POST /alerts/rules/bulk-delete`: Delete selected rules.
- `DELETE /alerts/rule/{rule_id}`: Delete one rule.
- `GET /alerts/{user_id}/events`: Recent alert events.
- `POST /alerts/{user_id}/evaluate`: Evaluate alert rules.
- `GET /news/{user_id}`: Portfolio-related news.
- `POST /news/{user_id}/ingest`: Ingest fresh news.

All AI and portfolio outputs are informational only and should not be considered financial advice.