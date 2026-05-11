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
    scan_status: str
    last_scan_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
