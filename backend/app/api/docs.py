from typing import Any
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import Endpoint, Repo
from app.core.openapi_assembler import OpenAPIAssembler

router = APIRouter()


def _get_user_id(request: Request) -> str:
    """Extract authenticated user_id from request state (set by CoreMiddleware)."""
    user_id: str | None = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


def _parse_user_id_int(user_id_str: str) -> int:
    try:
        return int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authentication user ID")


@router.get("/repos/{repo_id}/docs")
async def get_openapi_docs(
    repo_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    user_id = _get_user_id(request)
    user_int_id = _parse_user_id_int(user_id)
    try:
        repo_int_id = int(repo_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repo ID")

    repo_query = await db.execute(select(Repo).where(Repo.id == repo_int_id, Repo.user_id == user_int_id))
    if not repo_query.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    query = select(Endpoint).where(
        Endpoint.repo_id == repo_int_id,
        Endpoint.status == "approved",
    )
    result = await db.execute(query)
    endpoints = result.scalars().all()

    try:
        openapi_spec = OpenAPIAssembler.assemble(list(endpoints))
        return openapi_spec
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assemble OpenAPI spec: {str(e)}")


@router.get("/repos/{repo_id}/export")
async def export_docs(
    repo_id: str,
    request: Request,
    format: str = "markdown",
    db: AsyncSession = Depends(get_db),
) -> Any:
    user_id = _get_user_id(request)
    user_int_id = _parse_user_id_int(user_id)
    if format != "markdown":
        raise HTTPException(status_code=400, detail="Only markdown format is supported")

    try:
        repo_int_id = int(repo_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repo ID")

    repo_query = await db.execute(select(Repo).where(Repo.id == repo_int_id, Repo.user_id == user_int_id))
    if not repo_query.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    query = select(Endpoint).where(
        Endpoint.repo_id == repo_int_id,
        Endpoint.status == "approved",
    )
    result = await db.execute(query)
    endpoints = result.scalars().all()

    md_lines = [f"# API Documentation for Repository {repo_id}\n"]
    for ep in endpoints:
        doc = ep.generated_doc_json or {}
        md_lines.append(f"## {ep.method} {ep.path}")
        if "title" in doc:
            md_lines.append(f"**Summary**: {doc['title']}\n")
        if "description" in doc:
            md_lines.append(f"**Description**: {doc['description']}\n")
        if "parameters" in doc and doc["parameters"]:
            md_lines.append("### Parameters")
            md_lines.append("```json\n" + json.dumps(doc["parameters"], indent=2) + "\n```\n")
        if "request_body" in doc and doc["request_body"]:
            md_lines.append("### Request Body")
            md_lines.append("```json\n" + json.dumps(doc["request_body"], indent=2) + "\n```\n")
        if "responses" in doc and doc["responses"]:
            md_lines.append("### Responses")
            md_lines.append("```json\n" + json.dumps(doc["responses"], indent=2) + "\n```\n")

        md_lines.append("---\n")

    return PlainTextResponse("\n".join(md_lines), media_type="text/markdown")
