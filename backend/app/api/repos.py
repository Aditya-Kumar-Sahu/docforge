from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Repository
from app.schemas.repos import RepoCreate, RepoRead

router = APIRouter(prefix="/repos", tags=["repositories"])

@router.post("/", response_model=RepoRead, status_code=status.HTTP_201_CREATED)
async def create_repo(
    repo_in: RepoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if repo already exists for this user (or full_name is unique)
    query = select(Repository).where(Repository.full_name == repo_in.full_name)
    result = await db.execute(query)
    if result.scalars().first():
        # In a real app, we might just return the existing one or update it
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
    # Verify ownership
    query = select(Repository).where(Repository.id == repo_id, Repository.owner_id == current_user.id)
    result = await db.execute(query)
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Trigger Celery task (to be implemented)
    # scan_repo.delay(repo_id)
    return {"message": "Scan triggered", "repo_id": repo_id}
