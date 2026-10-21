"""
Unit tests for modules/ai/feature_engineering.py.
"""

import re

import numpy as np
import pandas as pd
import pytest

from modules.ai.client import AIResponse
from modules.ai.feature_engineering import (
    _fallback_suggestions,
    build_feature_engineering_prompt,
    generate_feature_engineering_suggestions,
)
from modules.eda import run_eda
from modules.profiler import profile_dataset


class _StubClient:
    def __init__(self, response: AIResponse):
        self._response = response

    def generate(self, prompt: str, max_retries: int = 3) -> AIResponse:
        return self._response


def _make_rich_dataset() -> pd.DataFrame:
    """A dataset deliberately shaped to trigger all 5 fallback suggestion
    types at once: binning, interaction, log-transform, date parts,
    and high-cardinality encoding."""
    np.random.seed(5)
    n = 200
    age = np.random.uniform(18, 80, n)
    experience = np.random.uniform(0, 20, n)
    salary = experience * 4000 + np.random.normal(0, 3000, n)  # strongly correlated w/ experience
    income = np.random.exponential(30000, n)  # genuinely skewed
    signup_date = pd.date_range("2023-01-01", periods=n)
    customer_id = [f"CUST{i:05d}" for i in range(n)]  # high cardinality

    return pd.DataFrame({
        "age": age, "experience": experience, "salary": salary,
        "income": income, "signup_date": signup_date, "customer_id": customer_id,
    })


def test_fallback_triggers_all_five_suggestion_types():
    df = _make_rich_dataset()
    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)

    result = _fallback_suggestions(profile, eda)

    assert "Bin `" in result
    assert "interaction feature" in result
    assert "Log-transform" in result
    assert "Extract date parts" in result
    assert "frequency encoding" in result


def test_fallback_never_invents_columns_not_in_the_dataset():
    df = _make_rich_dataset()
    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)

    result = _fallback_suggestions(profile, eda)

    mentioned = set(re.findall(r"`([a-zA-Z_0-9]+)`", result))
    real_columns = set(df.columns)

    assert mentioned - real_columns == set()  # nothing invented
    assert mentioned  # and it actually mentioned something real


def test_fallback_skips_binning_for_low_cardinality_numeric_column():
    """A column with only 3 distinct values (e.g. a 1-3 rating) doesn't
    need binning -- it's already effectively categorical."""
    df = pd.DataFrame({"rating": [1, 2, 3] * 20})
    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)

    result = _fallback_suggestions(profile, eda)

    assert "Bin `rating`" not in result


def test_fallback_reports_honestly_when_nothing_to_suggest():
    df = pd.DataFrame({"rating": [1, 2, 3] * 10})
    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)

    result = _fallback_suggestions(profile, eda)

    assert result == "No structural feature engineering opportunities were identified for this dataset."


def test_prompt_includes_column_lists():
    df = _make_rich_dataset()
    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)

    prompt = build_feature_engineering_prompt(profile, eda)

    assert "age" in prompt
    assert "customer_id" in prompt
    assert "do not invent columns" in prompt.lower()


def test_generate_returns_ai_text_on_success():
    df = _make_rich_dataset()
    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)
    client = _StubClient(AIResponse(success=True, text="AI suggestions here", attempts=1))

    result = generate_feature_engineering_suggestions(client, profile, eda)

    assert result == "AI suggestions here"


def test_generate_falls_back_on_failure():
    df = _make_rich_dataset()
    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)
    client = _StubClient(AIResponse(success=False, text="", error="down", attempts=3))

    result = generate_feature_engineering_suggestions(client, profile, eda)

    assert "customer_id" in result  # fell back to structural suggestions
