from typing import Dict

PROMPT_REGISTRY: Dict[str, str] = {
    "route_analyzer_v1": """
        ### ROLE
        You are an expert Backend Architect specializing in FastAPI. Your task is to analyze a raw AST representation of a FastAPI route and extract its semantic meaning.

        ### INPUT DATA (JSON AST)
        {code}

        ### GOAL
        Extract the following fields with high precision:
        1. **purpose**: A concise 1-sentence description (max 100 chars) of what this endpoint does from a user perspective.
        2. **action_type**: STRICTLY one of [CRUD, SEARCH, AUTH, STREAM, SYSTEM].
        3. **side_effects**: Detail any modifications to the database, external API calls, or background tasks. Use "None" if purely read-only.
        4. **auth_required**: Boolean. Set to true if `Depends` is used with an authentication-related function or if the router prefix suggests protection.

        ### OUTPUT FORMAT
        Return ONLY a valid JSON object. Do not include markdown formatting or preamble.
        {{
            "purpose": "string",
            "action_type": "string",
            "side_effects": "string",
            "auth_required": boolean
        }}
    """,
    "doc_generator_v1": """
        ### ROLE
        You are a Senior Technical Writer. Generate professional developer documentation for the following API endpoint based on its code and pre-analysis.

        ### INPUTS
        - **Pre-Analysis**: {analysis}
        - **Raw AST**: {code}

        ### REQUIREMENTS
        - **Title**: Format as "METHOD: /path" (e.g., "GET: /users/{{id}}").
        - **Description**: Use professional technical Markdown. Explain the business logic clearly.
        - **Parameters**: 
            - Extract all path, query, and body parameters.
            - For each, provide: name, type, and a helpful description.
            - If a Pydantic model is used, describe its fields.
        - **Response Example**: Provide a realistic JSON response body based on the expected return type.
        - **Code Example**: Provide a copy-pasteable Python example using the `httpx` library. Include imports and an async call.

        ### OUTPUT FORMAT
        Return ONLY a valid JSON object. Do not include markdown formatting outside the JSON fields.
        {{
            "title": "string",
            "description": "markdown_string",
            "parameters": [
                {{"name": "string", "type": "string", "description": "string", "in": "path|query|body"}}
            ],
            "response_example": "json_string",
            "code_example": "markdown_string"
        }}
    """,
    "quality_gate_v1": """
        ### ROLE
        You are a QA Lead and Security Auditor. Review the generated documentation against the original source code (AST).

        ### INPUTS
        - **Generated Docs**: {docs}
        - **Source Code (AST)**: {code}

        ### SCORING CRITERIA (1-10)
        - **Accuracy**: Does the documentation reflect the actual code logic and parameters perfectly?
        - **Completeness**: Are all parameters, return types, and side effects documented?
        - **Clarity**: Is the language professional, concise, and easy for a developer to follow?
        - **Security**: Does it properly mention auth requirements if they exist in the code?

        ### VERDICT
        - If Accuracy >= 8 and mean score >= 7.5, verdict is "approve".
        - Otherwise, verdict is "revise".

        ### OUTPUT FORMAT
        Return ONLY a valid JSON object.
        {{
            "scores": {{
                "accuracy": number,
                "completeness": number,
                "clarity": number,
                "security": number
            }},
            "mean_score": number,
            "verdict": "approve" | "revise",
            "reason": "Detailed explanation of why this verdict was reached, citing specific missing or incorrect details."
        }}
    """
}
