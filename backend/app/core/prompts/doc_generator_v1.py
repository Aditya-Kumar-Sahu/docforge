from langchain_core.prompts import ChatPromptTemplate

VERSION = "doc_generator_v1"

SYSTEM = """You are a technical writer producing Stripe-quality API documentation. 
You write clear, accurate, developer-friendly documentation.
Always respond with valid JSON only. No markdown, no explanation outside the JSON object."""

USER = """Generate comprehensive API documentation for this FastAPI endpoint. Return a JSON object with these exact keys:
- title: string (concise endpoint title, e.g. "Create User", "List Repositories")
- description: string (2-4 sentences: what it does, when to use it, any important notes)
- parameters: list of objects, each with: name, location ("path"|"query"|"body"), type, required (bool), description
- request_body: object or null (if POST/PUT/PATCH) with: description, required_fields list, optional_fields list, example (JSON object)
- responses: list of objects, each with: status_code (int), description, example (JSON object or null)
- code_examples: object with: curl (string), python (string)
- tags: list of strings (1-3 relevant tags for grouping)

Endpoint analysis:
- Purpose: {purpose}
- Action type: {action_type}
- Side effects: {side_effects}
- Auth required: {auth_required}

Route info:
- Method: {method}
- Path: {path}
- Path parameters: {path_parameters}
- Query parameters: {query_parameters}
- Request body model: {request_model}
- Response model: {response_model}

{fix_instructions}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", USER),
])
