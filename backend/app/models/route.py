from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ParsedRoute(BaseModel):
    method: str
    path: str
    handler_name: str
    file_path: str
    line_number: int
    path_parameters: List[Dict[str, Any]] = Field(default_factory=list)
    query_parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_model: Optional[Dict[str, Any]] = None
    response_model: Optional[Dict[str, Any]] = None
    docstring: Optional[str] = None
