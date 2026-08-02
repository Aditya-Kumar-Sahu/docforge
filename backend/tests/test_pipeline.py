"""
Tests for the 5-step LangChain AI pipeline.

All LLM calls are mocked — no real API calls are made.
We patch `_call_llm` directly (the lowest-level LLM invocation point)
to avoid needing to simulate LangChain's LCEL `prompt | llm` chaining.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.core.pipeline import (
    PROMPT_REGISTRY,
    GeneratedDoc,
    _parse_quality,
    run_pipeline,
)
from app.models.route import ParsedRoute


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_route() -> ParsedRoute:
    return ParsedRoute(
        method="GET",
        path="/api/users/{user_id}",
        handler_name="get_user",
        file_path="app/api/users.py",
        line_number=42,
        path_parameters=[{"name": "user_id", "type": "int"}],
        query_parameters=[],
        request_model=None,
        response_model={"type": "UserResponse"},
        docstring="Retrieve a user by ID.",
    )


@pytest.fixture
def mock_analysis() -> dict[str, Any]:
    return {
        "purpose": "Retrieves a user by their unique ID.",
        "action_type": "read",
        "side_effects": [],
        "auth_required": True,
        "complexity": "simple",
    }


@pytest.fixture
def mock_doc() -> dict[str, Any]:
    return {
        "title": "Get User",
        "description": "Retrieves a user record by their unique identifier.",
        "parameters": [
            {
                "name": "user_id",
                "location": "path",
                "type": "integer",
                "required": True,
                "description": "The user's unique ID.",
            }
        ],
        "request_body": None,
        "responses": [
            {
                "status_code": 200,
                "description": "User found",
                "example": {"id": 1, "email": "user@example.com"},
            }
        ],
        "code_examples": {
            "curl": "curl /api/users/1",
            "python": "requests.get('/api/users/1')",
        },
        "tags": ["users"],
    }


@pytest.fixture
def mock_quality_approve() -> dict[str, Any]:
    return {
        "accuracy": 9,
        "completeness": 8,
        "clarity": 9,
        "examples": 8,
        "tone": 8,
        "verdict": "approve",
        "fix_instructions": "",
        "mean_score": 8.4,
    }


@pytest.fixture
def mock_quality_revise() -> dict[str, Any]:
    return {
        "accuracy": 6,
        "completeness": 5,
        "clarity": 7,
        "examples": 5,
        "tone": 7,
        "verdict": "revise",
        "fix_instructions": "Add more detail to parameter descriptions.",
        "mean_score": 6.0,
    }


@pytest.fixture
def mock_quality_reject() -> dict[str, Any]:
    return {
        "accuracy": 3,
        "completeness": 4,
        "clarity": 3,
        "examples": 2,
        "tone": 4,
        "verdict": "reject",
        "fix_instructions": "Complete rewrite needed.",
        "mean_score": 3.2,
    }


# ── PROMPT_REGISTRY tests ─────────────────────────────────────────────────────

class TestPromptRegistry:
    def test_registry_has_all_versions(self) -> None:
        assert "route_analyzer_v1" in PROMPT_REGISTRY
        assert "doc_generator_v1" in PROMPT_REGISTRY
        assert "quality_gate_v1" in PROMPT_REGISTRY

    def test_registry_has_descriptions(self) -> None:
        for version, description in PROMPT_REGISTRY.items():
            assert len(description) > 10, f"{version} has an empty description"


# ── _parse_quality tests ──────────────────────────────────────────────────────

class TestParseQuality:
    def test_approve_verdict(self) -> None:
        raw = {
            "accuracy": 9,
            "completeness": 8,
            "clarity": 9,
            "examples": 8,
            "tone": 8,
            "fix_instructions": "",
        }
        result = _parse_quality(raw)
        assert result.verdict == "approve"
        assert result.mean_score >= 7.5

    def test_revise_verdict(self) -> None:
        raw = {
            "accuracy": 7,
            "completeness": 6,
            "clarity": 7,
            "examples": 6,
            "tone": 6,
            "fix_instructions": "Improve examples.",
        }
        result = _parse_quality(raw)
        assert result.verdict == "revise"

    def test_reject_verdict_low_mean(self) -> None:
        raw = {
            "accuracy": 3,
            "completeness": 4,
            "clarity": 3,
            "examples": 2,
            "tone": 4,
            "fix_instructions": "Rewrite.",
        }
        result = _parse_quality(raw)
        assert result.verdict == "reject"

    def test_revise_when_accuracy_below_threshold(self) -> None:
        """High mean but accuracy < 8 should produce revise, not approve."""
        raw = {
            "accuracy": 7,
            "completeness": 9,
            "clarity": 9,
            "examples": 9,
            "tone": 9,
            "fix_instructions": "Check accuracy.",
        }
        result = _parse_quality(raw)
        # mean = 8.6 but accuracy = 7 < 8.0 threshold
        assert result.verdict == "revise"

    def test_mean_score_computed_correctly(self) -> None:
        raw = {
            "accuracy": 8,
            "completeness": 8,
            "clarity": 8,
            "examples": 8,
            "tone": 8,
            "fix_instructions": "",
        }
        result = _parse_quality(raw)
        assert result.mean_score == 8.0


# ── run_pipeline integration tests (mocked at _call_llm) ─────────────────────

class TestRunPipeline:
    """
    We patch `app.core.pipeline._call_llm` so every LLM invocation
    (analyzer, generator, quality gate) can be controlled per-call
    without needing to simulate the LCEL `prompt | llm` operator chain.
    """

    @patch("app.core.pipeline._call_llm")
    @patch("app.core.pipeline.get_llm")
    def test_successful_first_attempt(
        self,
        mock_get_llm: MagicMock,
        mock_call_llm: MagicMock,
        sample_route: ParsedRoute,
        mock_analysis: dict[str, Any],
        mock_doc: dict[str, Any],
        mock_quality_approve: dict[str, Any],
    ) -> None:
        # _call_llm is called 3 times: analyzer, generator, quality gate
        mock_call_llm.side_effect = [mock_analysis, mock_doc, mock_quality_approve]
        mock_get_llm.return_value = MagicMock()

        result = run_pipeline(sample_route, "def get_user(): pass")

        assert result.final_verdict == "approved"
        assert result.attempts == 1
        assert result.needs_human_review is False
        assert result.generated_doc is not None
        assert result.quality_score is not None
        assert result.quality_score >= 7.5
        assert mock_call_llm.call_count == 3

    @patch("app.core.pipeline._call_llm")
    @patch("app.core.pipeline.get_llm")
    def test_retry_then_approve(
        self,
        mock_get_llm: MagicMock,
        mock_call_llm: MagicMock,
        sample_route: ParsedRoute,
        mock_analysis: dict[str, Any],
        mock_doc: dict[str, Any],
        mock_quality_revise: dict[str, Any],
        mock_quality_approve: dict[str, Any],
    ) -> None:
        # Calls: analyzer, gen1, quality(revise), gen2, quality(approve)
        mock_call_llm.side_effect = [
            mock_analysis,
            mock_doc,
            mock_quality_revise,
            mock_doc,
            mock_quality_approve,
        ]
        mock_get_llm.return_value = MagicMock()

        result = run_pipeline(sample_route, "def get_user(): pass")

        assert result.final_verdict == "approved"
        assert result.attempts == 2
        assert result.needs_human_review is False
        assert mock_call_llm.call_count == 5

    @patch("app.core.pipeline._call_llm")
    @patch("app.core.pipeline.get_llm")
    def test_exhausted_attempts_human_review(
        self,
        mock_get_llm: MagicMock,
        mock_call_llm: MagicMock,
        sample_route: ParsedRoute,
        mock_analysis: dict[str, Any],
        mock_doc: dict[str, Any],
        mock_quality_revise: dict[str, Any],
    ) -> None:
        # Calls: analyzer, gen, quality(revise) × 3 attempts
        mock_call_llm.side_effect = [
            mock_analysis,
            mock_doc, mock_quality_revise,
            mock_doc, mock_quality_revise,
            mock_doc, mock_quality_revise,
        ]
        mock_get_llm.return_value = MagicMock()

        result = run_pipeline(sample_route, "def get_user(): pass")

        assert result.needs_human_review is True
        assert result.final_verdict == "needs_human_review"
        assert result.attempts == 3

    @patch("app.core.pipeline._call_llm")
    @patch("app.core.pipeline.get_llm")
    def test_reject_then_human_review(
        self,
        mock_get_llm: MagicMock,
        mock_call_llm: MagicMock,
        sample_route: ParsedRoute,
        mock_analysis: dict[str, Any],
        mock_doc: dict[str, Any],
        mock_quality_reject: dict[str, Any],
    ) -> None:
        """Reject verdict should still consume retries and eventually flag human review."""
        mock_call_llm.side_effect = [
            mock_analysis,
            mock_doc, mock_quality_reject,
            mock_doc, mock_quality_reject,
            mock_doc, mock_quality_reject,
        ]
        mock_get_llm.return_value = MagicMock()

        result = run_pipeline(sample_route, "def get_user(): pass")

        assert result.needs_human_review is True
        assert result.attempts == 3

    @patch("app.core.pipeline.get_llm")
    def test_analyzer_failure_returns_human_review(
        self,
        mock_get_llm: MagicMock,
        sample_route: ParsedRoute,
    ) -> None:
        """If the LLM client itself raises on the analyzer step, return human_review immediately."""
        mock_get_llm.side_effect = Exception("API unreachable")

        result = run_pipeline(sample_route, "")

        assert result.needs_human_review is True
        assert result.attempts == 0
        assert result.final_verdict == "needs_human_review"

    @patch("app.core.pipeline._call_llm")
    @patch("app.core.pipeline.get_llm")
    def test_generator_exception_uses_fix_instructions(
        self,
        mock_get_llm: MagicMock,
        mock_call_llm: MagicMock,
        sample_route: ParsedRoute,
        mock_analysis: dict[str, Any],
        mock_doc: dict[str, Any],
        mock_quality_approve: dict[str, Any],
    ) -> None:
        """If generator raises on attempt 1, attempt 2 should still work."""
        mock_call_llm.side_effect = [
            mock_analysis,
            Exception("Transient error"),  # attempt 1 generator fails
            mock_doc,                       # attempt 2 generator succeeds
            mock_quality_approve,           # attempt 2 quality gate approves
        ]
        mock_get_llm.return_value = MagicMock()

        result = run_pipeline(sample_route, "def get_user(): pass")

        assert result.final_verdict == "approved"
        assert result.attempts == 2

    @patch("app.core.pipeline._call_llm")
    @patch("app.core.pipeline.get_llm")
    def test_prompt_versions_in_result(
        self,
        mock_get_llm: MagicMock,
        mock_call_llm: MagicMock,
        sample_route: ParsedRoute,
        mock_analysis: dict[str, Any],
        mock_doc: dict[str, Any],
        mock_quality_approve: dict[str, Any],
    ) -> None:
        mock_call_llm.side_effect = [mock_analysis, mock_doc, mock_quality_approve]
        mock_get_llm.return_value = MagicMock()

        result = run_pipeline(sample_route, "")

        assert "route_analyzer_v1" in result.prompt_versions
        assert "doc_generator_v1" in result.prompt_versions
        assert "quality_gate_v1" in result.prompt_versions

    @patch("app.core.pipeline._call_llm")
    @patch("app.core.pipeline.get_llm")
    def test_salvages_last_doc_on_exhaustion(
        self,
        mock_get_llm: MagicMock,
        mock_call_llm: MagicMock,
        sample_route: ParsedRoute,
        mock_analysis: dict[str, Any],
        mock_doc: dict[str, Any],
        mock_quality_revise: dict[str, Any],
    ) -> None:
        """After 3 failed attempts, the last generated doc is preserved in the result."""
        mock_call_llm.side_effect = [
            mock_analysis,
            mock_doc, mock_quality_revise,
            mock_doc, mock_quality_revise,
            mock_doc, mock_quality_revise,
        ]
        mock_get_llm.return_value = MagicMock()

        result = run_pipeline(sample_route, "")

        assert result.needs_human_review is True
        assert result.generated_doc is not None  # salvaged from last attempt
        assert isinstance(result.generated_doc, GeneratedDoc)
