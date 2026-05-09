from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class RepoBase(BaseModel):
    name: str
    full_name: str
    github_id: int

class RepoCreate(RepoBase):
    pass

class RepoRead(RepoBase):
    id: int
    owner_id: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
