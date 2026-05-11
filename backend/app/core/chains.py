import json
from typing import Any, Dict, Optional
from litellm import completion
from app.core.config import settings
from app.core.prompts import PROMPT_REGISTRY
import structlog

logger = structlog.get_logger()

async def analyze_route(raw_ast: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 1: Analyzes the raw AST data to understand the route's purpose.
    """
    prompt = PROMPT_REGISTRY["route_analyzer_v1"].format(
        code=json.dumps(raw_ast, indent=2)
    )
    
    try:
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error("analyze_route_failed", error=str(e))
        return {"error": str(e)}

async def generate_docs(analysis: Dict[str, Any], raw_ast: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2: Generates comprehensive documentation based on the analysis and AST.
    """
    prompt = PROMPT_REGISTRY["doc_generator_v1"].format(
        analysis=json.dumps(analysis, indent=2),
        code=json.dumps(raw_ast, indent=2)
    )
    
    try:
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error("generate_docs_failed", error=str(e))
        return {"error": str(e)}

async def run_quality_gate(docs: Dict[str, Any], raw_ast: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 3: Scores the generated documentation for accuracy and completeness.
    """
    prompt = PROMPT_REGISTRY["quality_gate_v1"].format(
        docs=json.dumps(docs, indent=2),
        code=json.dumps(raw_ast, indent=2)
    )
    
    try:
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error("quality_gate_failed", error=str(e))
        return {"score": 0, "reason": str(e)}

async def process_endpoint_pipeline(raw_ast: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full 5-Step Pipeline (Simplified for Phase 1 Sprint 2).
    """
    analysis = await analyze_route(raw_ast)
    if "error" in analysis:
        return {"status": "failed", "step": "analysis", "error": analysis["error"]}

    docs = await generate_docs(analysis, raw_ast)
    if "error" in docs:
        return {"status": "failed", "step": "generation", "error": docs["error"]}

    gate = await run_quality_gate(docs, raw_ast)
    
    return {
        "status": "success",
        "analysis": analysis,
        "documentation": docs,
        "gate": gate
    }
