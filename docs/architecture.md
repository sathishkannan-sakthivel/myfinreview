# FinReview Architecture

FinReview Community Edition is a self-hostable, AI-powered portfolio intelligence platform for Indian investors. The application uses a static browser frontend, a FastAPI backend, SQLModel persistence, market data provider integrations, news ingestion, alert evaluation, and optional OpenRouter-compatible AI briefings.

## 1. System Architecture

```mermaid
flowchart TB
    User["Investor / Reviewer"] --> Browser["Browser"]

    subgraph Frontend["Static Frontend"]
        UI["HTML + Bootstrap UI"]
        JS["Vanilla JavaScript App"]
        Charts["Chart.js Visualizations"]
        RuntimeConfig["Runtime API Config"]
    end

    subgraph Backend["FastAPI Backend"]
        API["REST API Routes"]
        Auth["Auth + Profile"]
        Portfolio["Portfolio Service"]
        Analytics["Analytics Service"]
        Alerts["Alerts Service"]
        News["News Service"]
        AI["AI Insight Service"]
        Reference["Reference Data Service"]
    end

    subgraph Persistence["Persistence"]
        DB[("SQLite Local / PostgreSQL Hosted")]
        PriceCache[("Price Cache")]
    end

    subgraph External["External Providers"]
        Yahoo["Yahoo Finance Compatible API"]
        MFAPI["mfapi.in"]
        RSS["RSS / NewsData.io"]
        OpenRouter["OpenRouter Compatible LLM"]
    end

    Browser --> UI
    UI --> JS
    JS --> RuntimeConfig
    JS -->|"HTTPS REST calls"| API

    API --> Auth
    API --> Portfolio
    API --> Analytics
    API --> Alerts
    API --> News
    API --> AI
    API --> Reference

    Auth --> DB
    Portfolio --> DB
    Portfolio --> PriceCache
    Analytics --> DB
    Alerts --> DB
    News --> DB
    AI --> DB

    Portfolio --> Yahoo
    Portfolio --> MFAPI
    News --> RSS
    AI --> OpenRouter
    Analytics --> Portfolio
    Alerts --> Portfolio
```

## 2. Portfolio Intelligence Flow

```mermaid
sequenceDiagram
    actor User as Investor
    participant UI as Static Frontend
    participant API as FastAPI API
    participant Portfolio as Portfolio Service
    participant Analytics as Analytics Service
    participant Alerts as Alerts Service
    participant News as News Service
    participant AI as AI Insight Service
    participant DB as SQLModel Database
    participant Providers as Market and AI Providers

    User->>UI: Add transaction or import CSV
    UI->>API: POST transaction data
    API->>Portfolio: Record BUY or SELL activity
    Portfolio->>Providers: Refresh latest prices when needed
    Portfolio->>DB: Persist transactions, holdings, price cache
    API->>Analytics: Recalculate valuation, XIRR, drift, concentration
    Analytics->>DB: Save analytics summary
    API->>Alerts: Evaluate price, valuation, and drift rules
    Alerts->>DB: Save alert events
    API-->>UI: Return updated portfolio response

    User->>UI: Refresh intelligence
    UI->>API: Generate insights and ingest news
    API->>News: Fetch portfolio-related news
    News->>Providers: Read RSS or news provider data
    News->>DB: Save categorized news
    API->>AI: Build portfolio context and request briefing
    AI->>Providers: Call OpenRouter compatible model
    AI->>DB: Save structured insights
    API-->>UI: Return news, alerts, analytics, and insights
```

## 3. AI Briefing Flow

```mermaid
flowchart LR
    Holdings["Holdings + Transactions"] --> Summary["Portfolio Summary"]
    Analytics["Analytics Summary"] --> Context["Prompt Context Builder"]
    Alerts["Recent Alert Events"] --> Context
    News["Portfolio News"] --> Context
    Summary --> Context

    Context --> Prompt["Structured AI Prompt"]
    Prompt --> LLM["OpenRouter Compatible Chat API"]
    LLM --> Response["Model Response"]
    Response --> Parser["Insight Normalization"]
    Parser --> Insights[("Stored Insights")]
    Insights --> UI["AI Briefing Modal"]

    Fallback["No API Key Configured"] --> Graceful["Graceful Unavailable Message"]
    Graceful --> UI
```

## 4. Deployment Topology

```mermaid
flowchart TB
    Visitor["Visitor Browser"] --> Domain["Portfolio Domain"]
    Domain --> MilesWeb["MilesWeb / Static PHP Hosting"]
    MilesWeb --> Frontend["FinReview Static Frontend"]
    Frontend --> Runtime["config.runtime.php"]
    Runtime --> APIOrigin["api.yourdomain.com"]

    APIOrigin --> Render["Render Web Service"]
    Render --> FastAPI["FastAPI + Uvicorn"]
    FastAPI --> Postgres[("Managed PostgreSQL")]
    FastAPI --> Providers["Market Data, News, OpenRouter"]

    GitHub["GitHub Repository"] --> Render
    GitHub --> MilesWeb

    Secrets["Environment Variables"] --> Render
    HostingEnv["FINREVIEW_API_URL"] --> Runtime
```

## Runtime Components

- `frontend/`: Static single-page application. It handles auth screens, dashboard, portfolio views, charts, transaction forms, alerts, market news, AI briefing display, and onboarding empty states.
- `frontend/config.runtime.example.php`: Optional shared-hosting runtime config pattern for injecting the public backend API origin without committing the real URL.
- `backend/main.py`: FastAPI application entrypoint, CORS setup, startup database initialization, and REST route composition.
- `backend/models/portable_models.py`: SQLModel schema for users, holdings, transactions, analytics, news, alerts, insights, and price cache.
- `backend/services/`: Portfolio, price, reference data, CAS parser boundary, and estimated overlap services.
- `backend/analytics/`: XIRR, concentration, allocation drift, and tax-loss diagnostics.
- `backend/ai/`: AI insight generation and provider calls.
- `backend/news/`: Market news ingestion, categorization, and sentiment enrichment.
- `backend/alerts/`: Portfolio, price, valuation, and allocation drift alert evaluation.

## Data Flow

1. A user registers or logs in through the static frontend.
2. The user imports CSV rows, loads the sample portfolio, or enters transactions manually.
3. Portfolio services persist transactions, update holdings, and refresh price metadata.
4. Analytics services calculate valuation, cost, XIRR, concentration, drift, estimated overlap preview, and tax-loss diagnostics.
5. Alert services evaluate explicit alert rules and target-allocation drift.
6. News services ingest portfolio-related market updates.
7. AI services generate informational summaries from portfolio context, analytics, alerts, and news when an AI provider key is configured.
8. The frontend renders charts, tables, diagnostics, alerts, news, AI insights, and empty states.

## Deployment Shape

- Local development can use SQLite and the Python static file server.
- Hosted backend deployments should use PostgreSQL because Render filesystem storage is ephemeral.
- The frontend is static and can be served by MilesWeb, any PHP-capable shared host, or any static host.
- A custom API subdomain such as `api.yourdomain.com` can point to Render so the public frontend does not expose the raw Render service URL.
- Secrets live in environment variables; the public API origin is runtime configuration, not a secret.