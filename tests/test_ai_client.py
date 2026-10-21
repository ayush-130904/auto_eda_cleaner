"""
Unit tests for modules/ai/client.py.

All tests use a fake, injected client (see the GeminiClient constructor's
`client` parameter) -- no real network calls or API key needed. This
proves the retry/error-handling logic works correctly; it does NOT prove
the real Gemini API integration works, since that requires a genuine
API key and a live network call, which isn't possible in this
environment. See the project README for how to verify that part
yourself locally.
"""

import pytest
from google.genai.errors import APIError

from modules.ai import client as client_module
from modules.ai.client import AIResponse, GeminiClient


@pytest.fixture(autouse=True)
def _no_real_sleeping(monkeypatch):
    """Retry logic uses time.sleep() for exponential backoff -- real
    delays would make this test file take 10+ seconds for no reason.
    Patched to a no-op for every test in this file automatically."""
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: None)


class _FakeResponse:
    """Mimics the shape of google.genai's real response object -- just
    the one attribute (.text) our code actually reads."""

    def __init__(self, text: str):
        self.text = text


class _FakeModels:
    """Mimics client.models -- generate_content() is scripted to return
    a sequence of canned outcomes, one per call, so tests can simulate
    failure-then-success sequences precisely."""

    def __init__(self, outcomes: list):
        self._outcomes = outcomes
        self.call_count = 0

    def generate_content(self, model: str, contents: str):
        outcome = self._outcomes[self.call_count]
        self.call_count += 1
        if isinstance(outcome, Exception):
            raise outcome
        return _FakeResponse(outcome)


class _FakeClient:
    def __init__(self, outcomes: list):
        self.models = _FakeModels(outcomes)


def _make_api_error(message: str) -> APIError:
    return APIError(code=429, response_json={"error": {"message": message}})


def test_generate_succeeds_on_first_try():
    fake_client = _FakeClient(["Median imputation was used because..."])
    client = GeminiClient(api_key="unused", model="gemini-3.5-flash", client=fake_client)

    result = client.generate("explain this")

    assert result.success is True
    assert result.text == "Median imputation was used because..."
    assert result.attempts == 1


def test_generate_retries_transient_api_errors_then_succeeds():
    fake_client = _FakeClient(
        [
            _make_api_error("rate limited"),
            _make_api_error("rate limited again"),
            "Finally succeeded",
        ]
    )
    client = GeminiClient(api_key="unused", model="gemini-3.5-flash", client=fake_client)

    result = client.generate("explain this", max_retries=3)

    assert result.success is True
    assert result.text == "Finally succeeded"
    assert result.attempts == 3
    assert fake_client.models.call_count == 3


def test_generate_fails_after_exhausting_all_retries():
    fake_client = _FakeClient(
        [
            _make_api_error("error 1"),
            _make_api_error("error 2"),
            _make_api_error("error 3"),
        ]
    )
    client = GeminiClient(api_key="unused", model="gemini-3.5-flash", client=fake_client)

    result = client.generate("explain this", max_retries=3)

    assert result.success is False
    assert "error 3" in result.error
    assert result.attempts == 3


def test_generate_retries_on_empty_response():
    fake_client = _FakeClient(["", "Real answer this time"])
    client = GeminiClient(api_key="unused", model="gemini-3.5-flash", client=fake_client)

    result = client.generate("explain this", max_retries=3)

    assert result.success is True
    assert result.text == "Real answer this time"
    assert result.attempts == 2


def test_generate_does_not_retry_non_api_exceptions():
    """A bug in our own code (e.g. TypeError) should fail immediately,
    not be retried three times as if it were a transient API problem."""
    fake_client = _FakeClient([TypeError("something in our own code is broken")])
    client = GeminiClient(api_key="unused", model="gemini-3.5-flash", client=fake_client)

    result = client.generate("explain this", max_retries=3)

    assert result.success is False
    assert "something in our own code is broken" in result.error
    assert result.attempts == 1  # did NOT retry
    assert fake_client.models.call_count == 1


def test_client_uses_injected_client_not_a_real_one():
    """Confirms the dependency-injection path is actually being used --
    if this test could somehow reach the network, it would hang or
    fail with an auth error instead of returning our canned response."""
    fake_client = _FakeClient(["injected client was used"])
    client = GeminiClient(api_key="totally-fake-key", model="gemini-3.5-flash", client=fake_client)

    result = client.generate("test")

    assert result.text == "injected client was used"
