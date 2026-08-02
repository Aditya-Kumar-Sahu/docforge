"""
DocForge 5-step LangChain AI pipeline.

Step 1 — Route Analyzer: extracts purpose, action type, side effects, auth
Step 2 — Doc Generator:  produces full structured documentation
Step 3 — Quality Gate:   scores accuracy/completeness/clarity/examples/tone
Retry loop: up to 3 attempts; fix_instructions injected into next attempt
After 3 failures: marks needs_human_review=True
"""

from __future__ import annotations

import json
import structlog
from typing import Any

from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.core.prompts.route_analyzer_v1 import (
    VERSION as ANALYZER_VERSION,
    prompt as analyzer_prompt,
)
from app.core.prompts.doc_generator_v1 import (
    VERSION as GENERATOR_VERSION,
    prompt as generator_prompt,
)
from app.core.prompts.quality_gate_v1 import (
    VERSION as QUALITY_VERSION,
    prompt as quality_prompt,
)
from app.models.route import ParsedRoute

log = structlog.get_logger()

MAX_ATTEMPTS = 3
APPROVE_MEAN_THRESHOLD = 7.5
APPROVE_ACCURACY_THRESHOLD = 8.0
REJECT_MEAN_THRESHOLD = 5.0

# Registry of all prompt versions used in the pipeline
PROMPT_REGISTRY: dict[str, str] = {
    ANALYZER_VERSION: "Step 1: Extracts route purpose, action type, side effects, auth requirement",
    GENERATOR_VERSION: "Step 2: Generates title, description, parameters, request/response, code examples",
    QUALITY_VERSION: "Step 3: Scores accuracy/completeness/clarity/examples/tone (each 1-10), produces verdict",
}


class QualityScore(BaseModel):
    accuracy: float
    completeness: float
    clarity: float
    examples: float
    tone: float
    mean_score: float
    verdict: str  # "approve" | "revise" | "reject"
    fix_instructions: str = ""


class GeneratedDoc(BaseModel):
    title: str
    description: str
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: list[dict[str, Any]] = Field(default_factory=list)
    code_examples: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    route_id: str  # {method}:{path}
    generated_doc: GeneratedDoc | None
    quality_score: float | None
    quality_dimensions: QualityScore | None
    attempts: int
    needs_human_review: bool
    final_verdict: str  # "approved" | "needs_human_review" | "failed"
    prompt_versions: dict[str, str]  # snapshot of PROMPT_REGISTRY used


def _call_llm(chain: Any, inputs: dict[str, Any]) -> dict[str, Any]:
    """Invoke a LangChain chain and parse the JSON response."""
    response = chain.invoke(inputs)
    content = response.content if hasattr(response, "content") else str(response)
    # Strip markdown code fences if LLM wraps in ```json ... ```
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
    return json.loads(content)  # type: ignore[no-any-return]


def _run_analyzer(route: ParsedRoute, source_code: str) -> dict[str, Any]:
    """Step 1: Analyze the route to extract structured metadata."""
    llm = get_llm(temperature=0.0)
    chain = analyzer_prompt | llm
    return _call_llm(chain, {
        "method": route.method,
        "path": route.path,
        "handler_name": route.handler_name,
        "path_parameters": json.dumps(route.path_parameters),
        "query_parameters": json.dumps(route.query_parameters),
        "request_model": json.dumps(route.request_model),
        "response_model": json.dumps(route.response_model),
        "docstring": route.docstring or "",
        "source_code": source_code,
    })


def _run_generator(
    route: ParsedRoute,
    analysis: dict[str, Any],
    fix_instructions: str = "",
) -> dict[str, Any]:
    """Step 2: Generate full API documentation."""
    llm = get_llm(temperature=0.2)
    chain = generator_prompt | llm
    return _call_llm(chain, {
        "method": route.method,
        "path": route.path,
        "path_parameters": json.dumps(route.path_parameters),
        "query_parameters": json.dumps(route.query_parameters),
        "request_model": json.dumps(route.request_model),
        "response_model": json.dumps(route.response_model),
        "purpose": analysis.get("purpose", ""),
        "action_type": analysis.get("action_type", ""),
        "side_effects": json.dumps(analysis.get("side_effects", [])),
        "auth_required": str(analysis.get("auth_required", False)),
        "fix_instructions": f"Previous attempt feedback to address:\n{fix_instructions}" if fix_instructions else "",
    })


def _run_quality_gate(route: ParsedRoute, generated_doc: dict[str, Any]) -> dict[str, Any]:
    """Step 3: Score the generated documentation."""
    llm = get_llm(temperature=0.0)
    chain = quality_prompt | llm
    return _call_llm(chain, {
        "method": route.method,
        "path": route.path,
        "generated_doc": json.dumps(generated_doc, indent=2),
    })


def _parse_quality(raw: dict[str, Any]) -> QualityScore:
    """Parse and validate quality gate output, computing mean if needed."""
    dims = ["accuracy", "completeness", "clarity", "examples", "tone"]
    scores = {d: float(raw.get(d, 0)) for d in dims}
    mean = round(sum(scores.values()) / len(dims), 2)
    
    # Enforce verdict logic regardless of what LLM returned
    if mean >= APPROVE_MEAN_THRESHOLD and scores["accuracy"] >= APPROVE_ACCURACY_THRESHOLD:
        verdict = "approve"
    elif mean >= REJECT_MEAN_THRESHOLD:
        verdict = "revise"
    else:
        verdict = "reject"
    
    return QualityScore(
        **scores,
        mean_score=mean,
        verdict=verdict,
        fix_instructions=raw.get("fix_instructions", ""),
    )


def run_pipeline(route: ParsedRoute, source_code: str) -> PipelineResult:
    """
    Orchestrate the full 5-step pipeline for a single route.
    
    Returns a PipelineResult with the generated doc, quality scores,
    attempt count, and whether human review is needed.
    """
    route_id = f"{route.method}:{route.path}"
    log.info("pipeline_started", route_id=route_id)
    
    generated_doc: GeneratedDoc | None = None
    quality: QualityScore | None = None
    attempt = 0
    fix_instructions = ""
    
    try:
        # Step 1: Analyze route (done once, not retried)
        analysis = _run_analyzer(route, source_code)
        log.info("pipeline_analysis_complete", route_id=route_id, action_type=analysis.get("action_type"))
    except Exception as exc:  # noqa: BLE001
        log.error("pipeline_analyzer_failed", route_id=route_id, error=str(exc))
        return PipelineResult(
            route_id=route_id,
            generated_doc=None,
            quality_score=None,
            quality_dimensions=None,
            attempts=0,
            needs_human_review=True,
            final_verdict="needs_human_review",
            prompt_versions=dict(PROMPT_REGISTRY),
        )
    
    # Steps 2+3: Generate → Quality Gate → Retry loop
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        log.info("pipeline_attempt", route_id=route_id, attempt=attempt)
        
        try:
            # Step 2: Generate doc
            raw_doc = _run_generator(route, analysis, fix_instructions)
            
            # Step 3: Quality gate
            raw_quality = _run_quality_gate(route, raw_doc)
            quality = _parse_quality(raw_quality)
            
            log.info(
                "pipeline_quality_scored",
                route_id=route_id,
                attempt=attempt,
                mean_score=quality.mean_score,
                verdict=quality.verdict,
            )
            
            if quality.verdict == "approve":
                generated_doc = GeneratedDoc(**raw_doc)
                return PipelineResult(
                    route_id=route_id,
                    generated_doc=generated_doc,
                    quality_score=quality.mean_score,
                    quality_dimensions=quality,
                    attempts=attempt,
                    needs_human_review=False,
                    final_verdict="approved",
                    prompt_versions=dict(PROMPT_REGISTRY),
                )
            
            # revise or reject — prepare fix_instructions for next attempt
            fix_instructions = quality.fix_instructions
            
            if quality.verdict == "reject" and attempt < MAX_ATTEMPTS:
                log.warning("pipeline_rejected", route_id=route_id, attempt=attempt, mean_score=quality.mean_score)
        
        except Exception as exc:  # noqa: BLE001
            log.error("pipeline_attempt_failed", route_id=route_id, attempt=attempt, error=str(exc))
            fix_instructions = f"Previous attempt raised an error: {exc}. Ensure all JSON fields are present and correctly formatted."
    
    # Exhausted all attempts
    log.warning("pipeline_human_review", route_id=route_id, attempts=attempt)
    
    # Try to salvage the last generated doc even if quality < threshold
    last_doc = None
    try:
        if raw_doc:
            last_doc = GeneratedDoc(**raw_doc)
    except Exception as salvage_exc:  # noqa: BLE001
        log.warning(
            "pipeline_salvage_failed",
            route_id=route_id,
            error=str(salvage_exc),
        )
    
    return PipelineResult(
        route_id=route_id,
        generated_doc=last_doc,
        quality_score=quality.mean_score if quality else None,
        quality_dimensions=quality,
        attempts=attempt,
        needs_human_review=True,
        final_verdict="needs_human_review",
        prompt_versions=dict(PROMPT_REGISTRY),
    )
