"""
LLM client configuration for DocForge.
Uses LiteLLM as a gateway to Gemini 2.0 Flash.
"""

import os
from langchain_litellm import ChatLiteLLM
from app.core.config import settings


def get_llm(temperature: float = 0.1) -> ChatLiteLLM:
    """Return a configured ChatLiteLLM instance."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")
    
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
    
    # LangSmith tracing
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = "docforge"
    
    return ChatLiteLLM(
        model=settings.LITELLM_MODEL,
        temperature=temperature,
        max_tokens=4096,
        max_retries=5,
    )
