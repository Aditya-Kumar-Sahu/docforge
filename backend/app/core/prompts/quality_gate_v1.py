from langchain_core.prompts import ChatPromptTemplate

VERSION = "quality_gate_v1"

SYSTEM = """You are a strict API documentation quality reviewer.
Score documentation on 5 dimensions. Always respond with valid JSON only."""

USER = """Review this API documentation and score it on each dimension from 1-10.

Return a JSON object with these exact keys:
- accuracy: integer 1-10 (does the doc accurately describe what the endpoint does?)
- completeness: integer 1-10 (are all parameters, responses, and edge cases documented?)
- clarity: integer 1-10 (is the language clear and unambiguous?)
- examples: integer 1-10 (are the code examples correct, realistic, and helpful?)
- tone: integer 1-10 (is the tone professional and developer-friendly like Stripe docs?)
- verdict: string ("approve" if mean>=7.5 AND accuracy>=8, "revise" if mean>=5 but fails approve, "reject" if mean<5)
- fix_instructions: string (specific actionable instructions for improvement, empty string if verdict is "approve")
- mean_score: float (arithmetic mean of all 5 scores, rounded to 2 decimal places)

Endpoint:
- Method: {method}
- Path: {path}

Generated documentation to review:
{generated_doc}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", USER),
])
