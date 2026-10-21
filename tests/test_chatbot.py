"""Unit tests for modules/ai/chatbot.py."""

import numpy as np
import pandas as pd
import pytest

from modules.ai.chatbot import ChatSession, ask_chatbot, build_system_context
from modules.ai.client import AIResponse
from modules.cleaner import auto_clean
from modules.eda import run_eda
from modules.profiler import profile_dataset
from modules.quality import assess_quality


class _StubClient:
    def __init__(self, texts):
        self.texts = texts
        self.calls = 0
        self.prompts_seen = []

    def generate(self, prompt, max_retries=3):
        self.prompts_seen.append(prompt)
        text = self.texts[self.calls]
        self.calls += 1
        return AIResponse(success=True, text=text, attempts=1)


def _make_session():
    df = pd.DataFrame({"age": [25, 30, 35]})
    cleaned_df, log = auto_clean(df)
    profile = profile_dataset(cleaned_df)
    quality = assess_quality(cleaned_df, profile)
    eda = run_eda(cleaned_df, profile.numerical_columns, profile.categorical_columns)
    context = build_system_context(profile, quality, log, eda, None)
    return ChatSession(system_context=context)


def test_system_context_uses_correct_grammar_for_single_column():
    df = pd.DataFrame({"age": [25, 30, 35]})
    cleaned_df, log = auto_clean(df)
    profile = profile_dataset(cleaned_df)
    quality = assess_quality(cleaned_df, profile)
    eda = run_eda(cleaned_df, profile.numerical_columns, profile.categorical_columns)

    context = build_system_context(profile, quality, log, eda, None)

    assert "1 column" in context
    assert "1 columns" not in context


def test_conversation_history_carries_into_second_prompt():
    session = _make_session()
    client = _StubClient(["First answer", "Second answer"])

    ask_chatbot(client, session, "How many rows?")
    ask_chatbot(client, session, "And columns?")

    second_prompt = client.prompts_seen[1]
    assert "How many rows?" in second_prompt
    assert "First answer" in second_prompt


def test_session_records_both_user_and_assistant_messages():
    session = _make_session()
    client = _StubClient(["An answer"])

    ask_chatbot(client, session, "A question")

    assert len(session.messages) == 2
    assert session.messages[0].role == "user"
    assert session.messages[1].role == "assistant"


def test_ask_chatbot_returns_honest_error_on_failure():
    session = _make_session()

    class FailingClient:
        def generate(self, prompt, max_retries=3):
            return AIResponse(success=False, text="", error="rate limited", attempts=3)

    result = ask_chatbot(FailingClient(), session, "A question")

    assert "couldn't reach" in result.lower()
    assert "rate limited" in result
    # the failure message should still be recorded in history, not silently dropped
    assert session.messages[-1].content == result
