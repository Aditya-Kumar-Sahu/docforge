from typing import Optional, Any
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

class QualityDimensions(BaseModel):
    accuracy: float
    completeness: float
    clarity: float
    examples: float
    tone: float
    mean_score: float
    verdict: str
    fix_instructions: str = ""

class GeneratedDocSchema(BaseModel):
    title: str
    description: str
    parameters: list[dict[str, Any]] = []
    request_body: Optional[dict[str, Any]] = None
    responses: list[dict[str, Any]] = []
    code_examples: dict[str, str] = {}
    tags: list[str] = []

class PipelineResultSchema(BaseModel):
    route_id: str
    generated_doc: Optional[GeneratedDocSchema] = None
    quality_score: Optional[float] = None
    quality_dimensions: Optional[QualityDimensions] = None
    attempts: int
    needs_human_review: bool
    final_verdict: str
    prompt_versions: dict[str, str] = {}
