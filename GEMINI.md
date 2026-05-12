# DocForge - Project Context

## Project Overview
DocForge is an AI-powered API documentation generator. It parses codebases (FastAPI, Express, Django, etc.) using AST parsing (tree-sitter) and uses LLMs (Gemini Flash via LangChain) to automatically generate Stripe-quality API documentation, OpenAPI 3.1 specs, and Markdown without requiring decorators or existing inline comments.

## Architecture & Tech Stack (Planned)
The project is designed as a monorepo with the following components:
- **Backend:** FastAPI (Python), managed by `uv`. Uses Celery for async tasks, LangChain for LLM orchestration, and Supabase Auth for JWT validation.
- **Frontend:** Next.js 14 (React), managed by `pnpm`. Uses TanStack Virtual and a Redoc component for docs preview.
- **CLI:** Python CLI using `typer` and `rich`, designed to be open-source and run locally to generate docs (`docforge generate`).
- **Database:** PostgreSQL 16 with the `pgvector` extension. Alembic for migrations.
- **Infrastructure:** Docker Compose for local orchestration (`api`, `frontend`, `postgres`, `redis`, `celery-worker`).

## Building and Running (Planned)
The infrastructure is currently being set up. The primary way to run the application locally will be:
```bash
docker compose up
```

## Development Conventions (Planned)
- **Package Management:** `uv` for Python (backend/CLI) and `pnpm` for Node.js (frontend).
- **Git Strategy:** Enforce `conventional commits` and prevent secrets in git history using `TruffleHog` pre-commit hooks.
- **Backend Quality:** `ruff` for linting, `mypy --strict` for type-checking, and `pytest` for testing (target ≥ 80% coverage).
- **Frontend Quality:** `ESLint` for linting, `tsc --noEmit` for type-checking, and `Vitest` for testing.
- **Logging:** `structlog` configured for JSON logging (including `request_id`, `user_id`, `endpoint`, `duration_ms`).
- **Configuration:** Pydantic v2 `Settings` loading from `.env`.
