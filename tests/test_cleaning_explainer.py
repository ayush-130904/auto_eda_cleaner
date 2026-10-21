"""
Unit tests for modules/ai/cleaning_explainer.py.

Uses a fake injected GeminiClient (no real network calls) to verify
both the successful-explanation path and the graceful-fallback path.
"""

import pytest
from datetime import datetime

from modules.ai.cleaning_explainer import (
    action_key,
    build_cleaning_explanation_prompt,
    explain_all_actions,
    explain_cleaning_action,
)
from modules.ai.client import AIResponse, GeminiClient
from modules.cleaner import CleaningAction


def _make_action(column="age", issue="missing values") -> CleaningAction:
    return CleaningAction(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        column=column,
        issue=issue,
        method="median imputation",
        reason="Column contains outliers; median is more robust than mean.",
        rows_affected=12,
        before_summary="12 missing values",
        after_summary="filled with median = 34.5",
    )


class _StubClient:
    """A GeminiClient-shaped stub: .generate() returns a pre-set
    AIResponse instead of calling any real client underneath."""

    def __init__(self, response: AIResponse):
        self._response = response
        self.last_prompt = None

    def generate(self, prompt: str, max_retries: int = 3) -> AIResponse:
        self.last_prompt = prompt
        return self._response


def test_prompt_includes_all_action_fields():
    action = _make_action()
    prompt = build_cleaning_explanation_prompt(action)

    assert "age" in prompt
    assert "missing values" in prompt
    assert "median imputation" in prompt
    assert "Column contains outliers" in prompt
    assert "12 missing values" in prompt


def test_explain_action_returns_ai_text_on_success():
    action = _make_action()
    fake_response = AIResponse(success=True, text="This matters because...", attempts=1)
    client = _StubClient(fake_response)

    result = explain_cleaning_action(client, action)

    assert result == "This matters because..."
    assert "age" in client.last_prompt  # confirms the real prompt was actually sent


def test_explain_action_falls_back_to_technical_reason_on_failure():
    action = _make_action()
    fake_response = AIResponse(success=False, text="", error="rate limited", attempts=3)
    client = _StubClient(fake_response)

    result = explain_cleaning_action(client, action)

    assert result == action.reason  # exact fallback, not an error message


def test_explain_all_actions_produces_unique_keys_for_same_column():
    """Regression-style test: mirrors the real Phase 5 case where
    'country' got two separate log entries (whitespace + casing)."""
    actions = [
        _make_action(column="country", issue="inconsistent whitespace"),
        _make_action(column="country", issue="inconsistent casing"),
    ]
    client = _StubClient(AIResponse(success=True, text="explanation", attempts=1))

    result = explain_all_actions(client, actions)

    assert len(result) == 2  # not silently overwritten down to 1
    assert len(set(result.keys())) == 2  # genuinely unique keys


def test_action_key_is_unique_even_for_identical_column_and_issue():
    """The page and explain_all_actions() must derive the exact same key
    for a given (action, index) pair, or lookups will silently miss."""
    action = _make_action(column="country", issue="inconsistent whitespace")
    assert action_key(action, 0) != action_key(action, 1)


def test_explain_all_actions_handles_empty_log():
    client = _StubClient(AIResponse(success=True, text="unused", attempts=1))
    result = explain_all_actions(client, [])
    assert result == {}
