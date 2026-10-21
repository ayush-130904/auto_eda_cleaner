"""
Unit tests for modules/eda.py.
"""

import numpy as np
import pandas as pd
import pytest

from modules.eda import (
    analyze_categorical_columns,
    analyze_correlations,
    analyze_numeric_columns,
    run_eda,
)


def test_numeric_stats_computed_correctly():
    df = pd.DataFrame({"age": [20, 30, 40, 50, 60]})
    stats = analyze_numeric_columns(df, ["age"])
    assert len(stats) == 1
    assert stats[0].mean == 40.0
    assert stats[0].median == 40.0
    assert stats[0].min == 20.0
    assert stats[0].max == 60.0


def test_numeric_stats_skips_all_missing_column():
    df = pd.DataFrame({"age": [np.nan, np.nan]})
    stats = analyze_numeric_columns(df, ["age"])
    assert stats == []


def test_categorical_stats_identifies_top_value():
    df = pd.DataFrame({"plan": ["free", "free", "free", "pro", "pro"]})
    stats = analyze_categorical_columns(df, ["plan"])
    assert stats[0].top_value == "free"
    assert stats[0].top_value_count == 3
    assert stats[0].top_value_pct == 60.0


def test_categorical_stats_limits_to_top_n():
    df = pd.DataFrame({"city": [f"city_{i}" for i in range(20)]})
    stats = analyze_categorical_columns(df, ["city"], top_n=5)
    assert len(stats[0].value_counts) == 5


def test_correlation_detects_strong_positive_relationship():
    np.random.seed(7)
    n = 200
    experience = np.random.uniform(0, 20, n)
    income = experience * 3000 + np.random.normal(0, 2000, n)
    age = np.random.uniform(22, 60, n)  # unrelated noise

    df = pd.DataFrame({"experience": experience, "income": income, "age": age})
    _, pairs = analyze_correlations(df, ["experience", "income", "age"])

    assert len(pairs) == 1
    pair = pairs[0]
    assert {pair.column_a, pair.column_b} == {"experience", "income"}
    assert pair.correlation > 0.5


def test_correlation_detects_negative_relationship():
    np.random.seed(3)
    n = 100
    price = np.random.uniform(10, 100, n)
    units_sold = 500 - price * 4 + np.random.normal(0, 20, n)

    df = pd.DataFrame({"price": price, "units_sold": units_sold})
    _, pairs = analyze_correlations(df, ["price", "units_sold"])

    assert pairs[0].correlation < 0
    assert "negative" in pairs[0].strength


def test_correlation_never_reports_a_pair_twice():
    np.random.seed(7)
    n = 100
    a = np.random.uniform(0, 10, n)
    b = a * 2 + np.random.normal(0, 0.5, n)
    df = pd.DataFrame({"a": a, "b": b})

    _, pairs = analyze_correlations(df, ["a", "b"])
    assert len(pairs) == 1  # not 2, even though the nested loop checks both orders


def test_correlation_handles_fewer_than_two_numeric_columns():
    df = pd.DataFrame({"price": [10, 20, 30]})
    matrix, pairs = analyze_correlations(df, ["price"])
    assert matrix.empty
    assert pairs == []


def test_run_eda_handles_zero_numeric_columns():
    df = pd.DataFrame({"label": ["x", "y", "z"]})
    result = run_eda(df, numerical_columns=[], categorical_columns=["label"])
    assert result.numeric_stats == []
    assert result.correlation_pairs == []
    assert len(result.categorical_stats) == 1
