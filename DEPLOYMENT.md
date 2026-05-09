# Deployment Runbook

## Local Development
1. Clone the repo.
2. Ensure Docker and Docker Compose are installed.
3. Copy `.env.example` to `.env` and fill in secrets.
4. Run `docker compose up`.
5. API will be at `http://localhost:8000`, Frontend at `http://localhost:3000`.

## Staging (Azure)
- Deployment is handled via GitHub Actions workflows triggered on every push to `main`.
- Backend and Frontend are deployed to Azure App Service as Docker containers.
- Environment variables and secrets are securely stored in Azure Key Vault and injected into App Service settings.
- The staging environment includes Azure Database for PostgreSQL and Azure Cache for Redis.

## Rollback
- To rollback staging, use the GitHub Actions "Re-run jobs" on a previous successful workflow run or trigger a deployment of a previous stable tag/commit.
- For database rollbacks, use `alembic downgrade -1` via a one-off task or shell in the backend container.
