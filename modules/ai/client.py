from __future__ import annotations

import time
from dataclasses import dataclass

from google import genai
from google.genai.errors import APIError


@dataclass(frozen=True)
class AIResponse:
    success: bool
    text: str
    error: str | None = None
    attempts: int = 1

class GeminiClient:
    def __init__(self, api_key: str, model: str, client: genai.Client | None = None):
        self.model = model
        self._client = client if client is not None else genai.Client(api_key=api_key)

    def generate(self, prompt: str, max_retries: int = 3) -> AIResponse:
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
                # Anything not from the SDK itself (e.g. a bug in our own
                # code) shouldn't be silently retried -- fail immediately
                # with the real error rather than masking a real bug
                # behind three identical retry attempts.
                return AIResponse(success=False, text="", error=str(exc), attempts=attempt)

        return AIResponse(success=False, text="", error=last_error, attempts=max_retries)