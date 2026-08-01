from pydantic import BaseModel

class RepoCreate(BaseModel):
    url: str

class RepoResponse(BaseModel):
    id: str
    url: str
    name: str

class ScanResponse(BaseModel):
    status: str

class ScanProgressResponse(BaseModel):
    status: str
    progress: int
