"""
Tests for the LLM client configuration.
"""

from unittest.mock import patch
import pytest


class TestGetLLM:
    def test_raises_on_missing_api_key(self) -> None:
        from app.core.llm import get_llm
        with patch("app.core.llm.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""
            mock_settings.LITELLM_MODEL = "gemini/gemini-2.0-flash"
            mock_settings.LANGSMITH_API_KEY = None
            
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                get_llm()

    def test_returns_chat_litellm_instance(self) -> None:
        from app.core.llm import get_llm
        from langchain_litellm import ChatLiteLLM
        
        with patch("app.core.llm.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "fake-key-for-test"
            mock_settings.LITELLM_MODEL = "gemini/gemini-2.0-flash"
            mock_settings.LANGSMITH_API_KEY = None
            
            llm = get_llm(temperature=0.1)
            assert isinstance(llm, ChatLiteLLM)

    def test_temperature_is_applied(self) -> None:
        from app.core.llm import get_llm
        
        with patch("app.core.llm.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "fake-key-for-test"
            mock_settings.LITELLM_MODEL = "gemini/gemini-2.0-flash"
            mock_settings.LANGSMITH_API_KEY = None
            
            llm = get_llm(temperature=0.7)
            assert llm.temperature == 0.7
