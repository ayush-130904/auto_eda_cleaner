"""
Gemini API client wrapper.

Wraps google.genai.Client with retry logic and a uniform AIResponse
shape, so every AI feature (cleaning explanations, executive summary,
business insights, chatbot) handles failures the same way instead of
each wrapping its own try/except around raw SDK calls.

Accepts an already-built client via the `client` parameter rather than
always constructing one internally -- this lets tests inject a fake
client and verify retry/error-handling behavior without ever touching
the real network or needing a real API key.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from google import genai
from google.genai.errors import APIError


@dataclass(frozen=True)
class AIResponse:
    """Uniform result shape for every Gemini call in this project."""

    success: bool
    text: str
    error: str | None = None
    attempts: int = 1


class GeminiClient:
    """Thin wrapper around google.genai.Client, adding retry logic and a
    uniform AIResponse shape."""

    def __init__(self, api_key: str, model: str, client: genai.Client | None = None):
        self.model = model
        self._client = client if client is not None else genai.Client(api_key=api_key)

    def generate(self, prompt: str, max_retries: int = 3) -> AIResponse:
        """Call Gemini with the given prompt, retrying transient API
        errors with exponential backoff. Non-API exceptions (bugs in our
        own code) fail immediately rather than being retried."""
        last_error = ""

        for attempt in range(1, max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                text = (response.text or "").strip()

                if not text:
                    last_error = "Model returned an empty response."
                    continue

                return AIResponse(success=True, text=text, attempts=attempt)

            except APIError as exc:
                last_error = str(exc)
                if attempt < max_retries:
                    time.sleep(2 ** (attempt - 1))  # 1s, 2s, 4s...

            except Exception as exc:  # noqa: BLE001
                # Not an SDK/API error -- likely a bug in our own code.
                # Fail immediately with the real error rather than
                # masking it behind repeated identical retry attempts.
                return AIResponse(success=False, text="", error=str(exc), attempts=attempt)

        return AIResponse(success=False, text="", error=last_error, attempts=max_retries)
