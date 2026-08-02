from langchain_core.prompts import ChatPromptTemplate

VERSION = "route_analyzer_v1"

SYSTEM = """You are an expert API documentation analyst. Analyze the given FastAPI route and extract structured information about it.
Always respond with valid JSON only. No markdown, no explanation outside the JSON object."""

USER = """Analyze this FastAPI route and return a JSON object with these exact keys:
- purpose: string (1-2 sentence description of what this endpoint does)
- action_type: string (one of: "create", "read", "update", "delete", "search", "auth", "webhook", "other")
- side_effects: list of strings (e.g. ["sends email", "updates database", "triggers background task"])
- auth_required: boolean (true if the endpoint requires authentication)
- complexity: string (one of: "simple", "moderate", "complex")

Route info:
- Method: {method}
- Path: {path}
- Handler: {handler_name}
- Path parameters: {path_parameters}
- Query parameters: {query_parameters}
- Request body model: {request_model}
- Response model: {response_model}
- Existing docstring: {docstring}

Source code:
```python
{source_code}
```"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", USER),
])
