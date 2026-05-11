from typing import Dict

PROMPT_REGISTRY: Dict[str, str] = {
    "route_analyzer_v1": """
        ### ROLE
        You are an expert Backend Architect. Your task is to analyze a raw AST representation of a FastAPI route and extract its semantic meaning.

        ### INPUT DATA (JSON AST)
        {code}

        ### GOAL
        Extract the following fields:
        1. **purpose**: A concise 1-sentence description of what this endpoint does.
        2. **action_type**: One of [CRUD, SEARCH, AUTH, STREAM, SYSTEM].
        3. **side_effects**: Does it modify the database, send emails, or trigger background tasks?
        4. **auth_required**: Does the code suggest authentication is required (e.g., Depends(get_current_user))?

        ### OUTPUT FORMAT
        Return ONLY a valid JSON object.
        {{
            "purpose": "string",
            "action_type": "string",
            "side_effects": "string",
            "auth_required": boolean
        }}
    """,
    "doc_generator_v1": """
        ### ROLE
        You are a Senior Technical Writer. Generate professional developer documentation for the following API endpoint.

        ### INPUTS
        - **Analysis**: {analysis}
        - **Raw AST**: {code}

        ### REQUIREMENTS
        - Use clear, professional Markdown.
        - Include a title starting with the HTTP method.
        - Describe all parameters (path, query, body).
        - Provide a mock response example.
        - Add a brief code example in Python using `httpx`.

        ### OUTPUT FORMAT
        Return ONLY a valid JSON object.
        {{
            "title": "string",
            "description": "markdown_string",
            "parameters": [
                {{"name": "string", "type": "string", "description": "string"}}
            ],
            "response_example": "json_string",
            "code_example": "markdown_string"
        }}
    """,
    "quality_gate_v1": """
        ### ROLE
        You are a QA Lead and Security Auditor. Review the generated documentation against the source code.

        ### INPUTS
        - **Generated Docs**: {docs}
        - **Source Code (AST)**: {code}

        ### SCORING CRITERIA (1-10)
        - **Accuracy**: Does it match the actual logic?
        - **Completeness**: Are all parameters documented?
        - **Clarity**: Is it easy to understand?
        - **Tone**: Is it professional?

        ### VERDICT
        - If Accuracy >= 7 and mean score >= 6.5, verdict is "approve".
        - Otherwise, verdict is "revise".

        ### OUTPUT FORMAT
        Return ONLY a valid JSON object.
        {{
            "scores": {{
                "accuracy": number,
                "completeness": number,
                "clarity": number,
                "tone": number
            }},
            "mean_score": number,
            "verdict": "approve" | "revise",
            "reason": "string"
        }}
    """
}
