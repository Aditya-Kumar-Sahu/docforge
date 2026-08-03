from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import Endpoint, Repo
from app.models.schemas import EndpointResponse, EndpointUpdateRequest, BulkApproveRequest, BulkApproveResponse

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


@router.get("/repos/{repo_id}/endpoints", response_model=List[EndpointResponse])
async def list_endpoints(
    repo_id: str,
    request: Request,
    status: str | None = None,
    file_path: str | None = None,
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

    query = select(Endpoint).where(Endpoint.repo_id == repo_int_id)
    if status:
        query = query.where(Endpoint.status == status)
    if file_path:
        query = query.where(Endpoint.file_path.ilike(f"%{file_path}%"))

    result = await db.execute(query)
    endpoints = result.scalars().all()
    return endpoints


@router.patch("/endpoints/{endpoint_id}/approve", response_model=EndpointResponse)
async def approve_endpoint(
    endpoint_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    user_id = _get_user_id(request)
    user_int_id = _parse_user_id_int(user_id)
    ep_query = await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    ep = ep_query.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    repo_query = await db.execute(select(Repo).where(Repo.id == ep.repo_id, Repo.user_id == user_int_id))
    if not repo_query.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    ep.status = "approved"
    ep.needs_human_review = False
    await db.commit()
    await db.refresh(ep)
    return ep


@router.patch("/endpoints/{endpoint_id}/reject", response_model=EndpointResponse)
async def reject_endpoint(
    endpoint_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    user_id = _get_user_id(request)
    user_int_id = _parse_user_id_int(user_id)
    ep_query = await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    ep = ep_query.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    repo_query = await db.execute(select(Repo).where(Repo.id == ep.repo_id, Repo.user_id == user_int_id))
    if not repo_query.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    ep.status = "rejected"
    ep.needs_human_review = True
    await db.commit()
    await db.refresh(ep)
    return ep


@router.patch("/endpoints/{endpoint_id}", response_model=EndpointResponse)
async def update_endpoint_doc(
    endpoint_id: int,
    req: EndpointUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    user_id = _get_user_id(request)
    user_int_id = _parse_user_id_int(user_id)
    ep_query = await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    ep = ep_query.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    repo_query = await db.execute(select(Repo).where(Repo.id == ep.repo_id, Repo.user_id == user_int_id))
    if not repo_query.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    if ep.generated_doc_json:
        doc = dict(ep.generated_doc_json)
    else:
        doc = {}

    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        doc[k] = v

    ep.generated_doc_json = doc
    await db.commit()
    await db.refresh(ep)
    return ep


@router.post("/repos/{repo_id}/endpoints/bulk-approve", response_model=BulkApproveResponse)
async def bulk_approve_endpoints(
    repo_id: str,
    req: BulkApproveRequest,
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
        Endpoint.quality_score >= req.min_quality_score,
        Endpoint.status != "approved",
    )
    result = await db.execute(query)
    endpoints = result.scalars().all()

    approved_ids = []
    for ep in endpoints:
        ep.status = "approved"
        ep.needs_human_review = False
        approved_ids.append(ep.id)

    await db.commit()

    return BulkApproveResponse(approved_count=len(approved_ids), endpoint_ids=approved_ids)
