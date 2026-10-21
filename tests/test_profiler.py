"""
Unit tests for modules/profiler.py.
"""

import numpy as np
import pandas as pd
import pytest

from modules.profiler import profile_dataset


def test_profile_counts_rows_and_columns_correctly():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    profile = profile_dataset(df)
    assert profile.n_rows == 3
    assert profile.n_columns == 2


def test_profile_detects_duplicate_rows():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    profile = profile_dataset(df)
    assert profile.duplicate_rows == 1


def test_profile_detects_missing_values():
    df = pd.DataFrame({"a": [1, np.nan, 3, np.nan]})
    profile = profile_dataset(df)
    col = profile.columns[0]
    assert col.missing_count == 2
    assert col.missing_pct == 50.0


def test_profile_flags_constant_column():
    df = pd.DataFrame({"country": ["India"] * 10, "age": range(10)})
    profile = profile_dataset(df)
    assert profile.constant_columns == ["country"]


def test_profile_classifies_column_types_correctly():
    df = pd.DataFrame(
        {
            "age": [25, 30, 40],
            "plan": ["free", "pro", "free"],
            "signup_date": pd.date_range("2024-01-01", periods=3),
        }
    )
    profile = profile_dataset(df)
    assert profile.numerical_columns == ["age"]
    assert profile.categorical_columns == ["plan"]
    assert profile.date_columns == ["signup_date"]


def test_high_cardinality_never_flags_date_columns():
    """
    Regression test: date columns are naturally all-unique, which used
    to incorrectly trigger the high-cardinality flag. This test locks
    in the fix so it can never silently break again.
    """
    n = 100
    df = pd.DataFrame(
        {
            "customer_id": [f"CUST{i:04d}" for i in range(n)],
            "signup_date": pd.date_range("2024-01-01", periods=n),
        }
    )
    profile = profile_dataset(df)
    assert "customer_id" in profile.high_cardinality_columns
    assert "signup_date" not in profile.high_cardinality_columns


def test_profile_handles_empty_dataframe_without_crashing():
    df = pd.DataFrame({"a": [], "b": []})
    profile = profile_dataset(df)
    assert profile.n_rows == 0
    assert profile.duplicate_pct == 0.0
