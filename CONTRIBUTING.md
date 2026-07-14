# Contributing

Thanks for helping improve FinReview.

## Local Setup

1. Create a Python 3.11+ virtual environment.
2. Install backend dependencies: `pip install -r backend/requirements.txt`.
3. Copy `.env.example` to `backend/.env` or export the same variables in your shell.
4. Run the API from `backend/`: `uvicorn main:app --reload`.
5. Serve the frontend from `frontend/`: `python -m http.server 8080`.

## Pull Requests

- Keep changes focused and explain the user or maintainer impact.
- Add tests for backend logic changes.
- Do not commit local databases, logs, provider keys, or generated cache files.
- Keep financial outputs informational; do not add advisory language.

## Code Style

Prefer small service-level changes, SQLModel models for persistence, and clear REST contracts from `backend/main.py`.