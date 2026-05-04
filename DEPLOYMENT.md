# Deployment Runbook

## Local Development
1. Clone the repo.
2. Ensure Docker and Docker Compose are installed.
3. Copy `backend/.env.example` to `backend/.env` and fill in secrets.
4. Run `docker compose up`.
5. API will be at `http://localhost:8000`, Frontend at `http://localhost:3000`.

## Staging (Railway)
- The project is configured for auto-deployment to Railway on every push to `main`.
- Environment variables are managed in the Railway dashboard.

## Rollback
- To rollback staging, use the Railway CLI or Dashboard to redeploy a previous successful build.
- For database rollbacks, use `alembic downgrade -1`.
