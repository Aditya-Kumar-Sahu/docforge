from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class RouteParam(BaseModel):
    name: str
    type: str
    schema_data: Optional[Dict[str, Any]] = Field(None, alias="schema")

class ParsedRoute(BaseModel):
    method: str
    path: str
    handler_name: str
    file_path: str
    line_number: int
    params: List[RouteParam]
    docstring: Optional[str] = None
