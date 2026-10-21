"""
Unit tests for modules/ai/executive_summary.py.
"""

import numpy as np
import pandas as pd
import pytest

from modules.ai.client import AIResponse
from modules.ai.executive_summary import (
    _fallback_summary,
    build_executive_summary_prompt,
    generate_executive_summary,
)
from modules.cleaner import CleaningLog, auto_clean
from modules.eda import run_eda
from modules.profiler import profile_dataset
from modules.quality import assess_quality


class _StubClient:
    def __init__(self, response: AIResponse):
        self._response = response
        self.last_prompt = None

    def generate(self, prompt: str, max_retries: int = 3) -> AIResponse:
        self.last_prompt = prompt
        return self._response


def _make_pipeline_outputs():
    np.random.seed(1)
    n = 100
    age = list(np.random.randint(20, 60, n))
    age[0] = 9999
    country = list(np.random.choice(["india", "India", "INDIA"], n))
    income = np.random.uniform(30000, 90000, n)

    df = pd.DataFrame({"age": age, "country": country, "income": income})
    df.loc[10:14, "age"] = np.nan

    cleaned_df, log = auto_clean(df)
    profile = profile_dataset(cleaned_df)
    quality = assess_quality(cleaned_df, profile)
    eda = run_eda(cleaned_df, profile.numerical_columns, profile.categorical_columns)

    return profile, quality, log, eda


def test_prompt_includes_row_count_and_quality_score():
    profile, quality, log, eda = _make_pipeline_outputs()
    prompt = build_executive_summary_prompt(profile, quality, log, eda)

    assert str(profile.n_rows) in prompt
    assert str(quality.overall_score) in prompt


def test_generate_returns_ai_text_on_success():
    profile, quality, log, eda = _make_pipeline_outputs()
    client = _StubClient(AIResponse(success=True, text="AI-written summary", attempts=1))

    result = generate_executive_summary(client, profile, quality, log, eda)

    assert result == "AI-written summary"


def test_generate_falls_back_on_ai_failure():
    profile, quality, log, eda = _make_pipeline_outputs()
    client = _StubClient(AIResponse(success=False, text="", error="rate limited", attempts=3))

    result = generate_executive_summary(client, profile, quality, log, eda)

    assert str(profile.n_rows) in result
    assert "%" in result  # quality percentage mentioned


def test_fallback_deduplicates_repeated_issue_types_across_columns():
    """Two different columns sharing the same issue type (e.g. both
    have 'missing values') should only be mentioned once, not twice."""
    log = CleaningLog()
    log.add(
        column="age", issue="missing values", method="median imputation",
        reason="r1", rows_affected=5, before_summary="b1", after_summary="a1",
    )
    log.add(
        column="income", issue="missing values", method="mean imputation",
        reason="r2", rows_affected=3, before_summary="b2", after_summary="a2",
    )

    df = pd.DataFrame({"age": range(20), "income": range(20)})
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)

    result = _fallback_summary(profile, quality, log)

    assert result.count("missing values") == 1
    assert "2 automated cleaning actions were applied" in result  # count itself is still accurate


def test_fallback_handles_empty_cleaning_log():
    df = pd.DataFrame({"age": range(20)})
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    log = CleaningLog()

    result = _fallback_summary(profile, quality, log)

    assert "No cleaning was necessary" in result


def test_fallback_quality_word_matches_score_tier():
    df = pd.DataFrame({"age": range(20)})
    profile = profile_dataset(df)
    log = CleaningLog()

    excellent_quality = assess_quality(df, profile)  # clean data -> 100%
    result = _fallback_summary(profile, excellent_quality, log)
    assert "excellent" in result


def test_fallback_uses_correct_grammar_for_singular_counts():
    """Regression test: caught via a real AppTest run where a 1-column
    dataset produced 'This dataset contains 29 rows and 1 columns.' --
    grammatically wrong. Locks in the fix for row/column/action counts
    of exactly 1."""
    df = pd.DataFrame({"age": [25]})
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    log = CleaningLog()
    log.add(
        column="age", issue="missing values", method="m", reason="r",
        rows_affected=1, before_summary="b", after_summary="a",
    )

    result = _fallback_summary(profile, quality, log)

    assert "1 row and 1 column." in result
    assert "1 automated cleaning action was applied" in result
    assert "columns" not in result  # would indicate the bug regressed
    assert "actions were" not in result


def test_fallback_uses_correct_grammar_for_plural_counts():
    df = pd.DataFrame({"age": range(20), "income": range(20)})
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    log = CleaningLog()
    log.add(
        column="age", issue="missing values", method="m", reason="r",
        rows_affected=1, before_summary="b", after_summary="a",
    )
    log.add(
        column="income", issue="outliers", method="m", reason="r",
        rows_affected=1, before_summary="b", after_summary="a",
    )

    result = _fallback_summary(profile, quality, log)

    assert "20 rows and 2 columns." in result
    assert "2 automated cleaning actions were applied" in result
