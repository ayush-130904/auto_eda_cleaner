"""
Unit tests for modules/ai/business_insights.py.
"""

import numpy as np
import pandas as pd
import pytest

from modules.ai.business_insights import (
    _fallback_insights,
    _gather_context,
    build_business_insights_prompt,
    generate_business_insights,
)
from modules.ai.client import AIResponse
from modules.eda import run_eda
from modules.profiler import profile_dataset
from modules.quality import assess_quality


class _StubClient:
    def __init__(self, response: AIResponse):
        self._response = response

    def generate(self, prompt: str, max_retries: int = 3) -> AIResponse:
        return self._response


def test_fallback_flags_category_at_exactly_50_percent():
    df = pd.DataFrame({
        "plan_dominant": ["free"] * 50 + ["pro"] * 50,
        "plan_balanced": (["a", "b", "c"] * 33) + ["a"],
    })
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)

    result = _fallback_insights(quality, eda)

    assert "plan_dominant" in result
    assert "plan_balanced" not in result


def test_fallback_reports_no_notable_patterns_honestly():
    df = pd.DataFrame({"category": ["a", "b", "c", "d"] * 25})
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)

    result = _fallback_insights(quality, eda)

    assert result == "No notable patterns were found in this dataset."


def test_skewness_translated_correctly_in_context():
    np.random.seed(3)
    income = np.random.exponential(30000, 200)  # genuinely right-skewed
    age = np.random.normal(40, 10, 200)  # genuinely symmetric

    df = pd.DataFrame({"income": income, "age": age})
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)

    context = _gather_context(quality, eda)

    assert "income: right-skewed" in context
    assert "age: roughly symmetric" in context


def test_generate_returns_ai_text_on_success():
    df = pd.DataFrame({"age": range(20)})
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)
    client = _StubClient(AIResponse(success=True, text="AI insights here", attempts=1))

    result = generate_business_insights(client, quality, eda)

    assert result == "AI insights here"


def test_generate_falls_back_on_failure():
    df = pd.DataFrame({
        "plan": ["free"] * 60 + ["pro"] * 40,
    })
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)
    client = _StubClient(AIResponse(success=False, text="", error="down", attempts=3))

    result = generate_business_insights(client, quality, eda)

    assert "plan" in result
    assert "60.0%" in result


def test_fallback_caps_outlier_summary_to_three_columns():
    quality_data = {"outlier_columns": {f"col_{i}": i for i in range(6)}}

    class FakeQuality:
        outlier_columns = {f"col_{i}": i for i in range(6)}

    class FakeEDA:
        correlation_pairs = []
        categorical_stats = []

    result = _fallback_insights(FakeQuality(), FakeEDA())

    # only the first 3 of 6 outlier columns should be mentioned
    mentioned = sum(1 for i in range(6) if f"col_{i}" in result)
    assert mentioned == 3
