# Changelog

All notable changes to FinReview are documented here.

## [1.0.0] - 2026-07-13

### Added
- Community Edition release posture with all portfolio intelligence features available to registered users.
- Optional sample portfolio loader for first-run exploration.
- Open-source release docs, Docker files, environment template, and CI workflow.

### Changed
- Simplified the application into a fully available Community Edition with no artificial feature locks.
- Rewrote architecture documentation to match the active FastAPI and SQLModel implementation.
- Removed committed provider secrets and moved runtime values to environment variables.

### Fixed
- Added missing `AnalyticsSummary.data_json` model field used by analytics persistence.
- Made duplicate transaction hashes user- and transaction-type-aware.