import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, AsyncGenerator, Dict, Any
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Repository, Endpoint
from app.schemas.repos import RepoCreate, RepoRead
from app.schemas.parser import EndpointRead, EndpointUpdate
from app.worker import scan_repo

router = APIRouter(prefix="/repos", tags=["repositories"])

@router.post("/", response_model=RepoRead, status_code=status.HTTP_201_CREATED)
async def create_repo(
    repo_in: RepoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Repository).where(Repository.full_name == repo_in.full_name)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Repository already registered")
    
    new_repo = Repository(
        owner_id=current_user.id,
        name=repo_in.name,
        full_name=repo_in.full_name,
        github_id=repo_in.github_id,
        is_active=True
    )
    db.add(new_repo)
    await db.commit()
    await db.refresh(new_repo)
    return new_repo

@router.get("/", response_model=List[RepoRead])
async def list_repos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Repository).where(Repository.owner_id == current_user.id, Repository.deleted_at == None)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/{repo_id}/scan")
async def trigger_scan(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Repository).where(Repository.id == repo_id, Repository.owner_id == current_user.id)
    result = await db.execute(query)
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Update status to scanning
    repo.scan_status = "scanning"
    await db.commit()
    
    # Trigger Celery task
    scan_repo.delay(repo_id)
    return {"message": "Scan triggered", "repo_id": repo_id}

@router.get("/{repo_id}/scan-progress")
async def scan_progress(
    repo_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    query = select(Repository).where(Repository.id == repo_id, Repository.owner_id == current_user.id)
    result = await db.execute(query)
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    async def event_generator() -> AsyncGenerator[Dict[str, Any], None]:
        while True:
            # If client closes connection, stop
            if await request.is_disconnected():
                break

            # Poll database for status
            # We need a new session or refresh the object
            async with AsyncSession(db.bind, expire_on_commit=False) as poll_session:
                q = select(Repository).where(Repository.id == repo_id)
                res = await poll_session.execute(q)
                current_repo = res.scalars().first()
                
                if current_repo:
                    yield {
                        "event": "message",
                        "id": str(repo_id),
                        "data": json.dumps({
                            "status": current_repo.scan_status,
                            "repo_id": repo_id
                        })
                    }
                    
                    if current_repo.scan_status in ["completed", "failed"]:
                        break

            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())

@router.get("/{repo_id}/endpoints", response_model=List[EndpointRead])
async def list_endpoints(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    query = select(Repository).where(Repository.id == repo_id, Repository.owner_id == current_user.id)
    result = await db.execute(query)
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Repository not found")

    query = select(Endpoint).where(Endpoint.repo_id == repo_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/endpoints/{endpoint_id}", response_model=EndpointRead)
async def get_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Endpoint).join(Repository).where(
        Endpoint.id == endpoint_id,
        Repository.owner_id == current_user.id
    )
    result = await db.execute(query)
    endpoint = result.scalars().first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return endpoint

@router.patch("/endpoints/{endpoint_id}", response_model=EndpointRead)
async def update_endpoint(
    endpoint_id: int,
    endpoint_in: EndpointUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Endpoint).join(Repository).where(
        Endpoint.id == endpoint_id,
        Repository.owner_id == current_user.id
    )
    result = await db.execute(query)
    endpoint = result.scalars().first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    update_data = endpoint_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(endpoint, field, value)
    
    await db.commit()
    await db.refresh(endpoint)
    return endpoint
