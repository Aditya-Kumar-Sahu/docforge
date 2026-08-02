"""
LangChain pipeline integration for DocForge.

This module provides the public API for the AI pipeline.
Actual implementation is in app.core.pipeline.
"""

from typing import Any
from app.core.pipeline import run_pipeline, PROMPT_REGISTRY, PipelineResult

__all__ = ["run_pipeline", "PROMPT_REGISTRY", "PipelineResult"]


def generate_endpoint_docs_chain(route_info: dict[str, Any]) -> dict[str, Any]:
    """Legacy stub — use run_pipeline() directly for new code."""
    return {"description": "Use run_pipeline() for AI-powered docs", "summary": ""}


def review_docs_chain(doc_json: dict[str, Any]) -> dict[str, Any]:
    """Legacy stub — quality gate is integrated into run_pipeline()."""
    return {"status": "use run_pipeline()", "comments": []}


def update_openapi_spec_chain(existing_spec: dict[str, Any], new_endpoint: dict[str, Any]) -> dict[str, Any]:
    """Legacy stub — OpenAPIAssembler (Sprint 3) will handle spec assembly."""
    return existing_spec


def generate_markdown_docs_chain(openapi_spec: dict[str, Any]) -> str:
    """Legacy stub — Markdown export (Sprint 3) will handle this."""
    return "# API Documentation\n\nComing soon."


def extract_schema_chain(model_code: str) -> dict[str, Any]:
    """Legacy stub — full JSON Schema extraction planned for Sprint 3."""
    return {"type": "object", "properties": {}}
