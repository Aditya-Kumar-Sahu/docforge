from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

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

class EndpointResponse(BaseModel):
    id: int
    repo_id: int | str
    method: str
    path: str
    handler_function: str
    file_path: str
    line_number: int
    status: str
    quality_score: float | None = None
    quality_dimensions: dict[str, Any] | None = None
    attempts: int
    needs_human_review: bool
    source_code_snippet: str | None = None
    params_json: dict[str, Any] | None = None
    response_schema_json: dict[str, Any] | None = None
    generated_doc_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EndpointUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    parameters: list[dict[str, Any]] | None = None
    request_body: dict[str, Any] | None = None
    responses: list[dict[str, Any]] | None = None

class BulkApproveRequest(BaseModel):
    min_quality_score: float = 7.0

class BulkApproveResponse(BaseModel):
    approved_count: int
    endpoint_ids: list[int]
