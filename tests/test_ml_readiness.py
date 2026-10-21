"""
Unit tests for modules/ml_readiness.py.
"""

import numpy as np
import pandas as pd
import pytest

from modules.eda import run_eda
from modules.ml_readiness import (
    _check_target_leakage,
    assess_ml_readiness,
)
from modules.profiler import profile_dataset
from modules.quality import assess_quality


def _pipeline(df, target_column=None):
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)
    return assess_ml_readiness(df, profile, quality, eda, target_column=target_column)


def test_clean_balanced_dataset_scores_high():
    np.random.seed(9)
    df = pd.DataFrame({
        "age": np.random.uniform(20, 60, 200),
        "income": np.random.uniform(30000, 90000, 200),
        "target": np.random.choice(["yes", "no"], 200),
    })
    result = _pipeline(df, target_column="target")
    assert result.readiness_score >= 85


def test_missing_values_detected_and_penalized():
    df = pd.DataFrame({"age": [25, 30, np.nan, 40]})
    result = _pipeline(df)
    categories = [i.category for i in result.issues]
    assert "Missing Values" in categories


def test_target_column_excluded_from_general_feature_checks():
    """
    Regression test: the target column used to appear in 'Encoding
    Needed' right alongside real feature columns, which is misleading --
    the target isn't a feature to preprocess the same way. Caught via
    a real messy-dataset test; locks in the fix.
    """
    np.random.seed(2)
    n = 300
    plan = np.random.choice(["free"] * 90 + ["pro"] * 10, n)
    target = np.random.choice(["churned"] * 95 + ["stayed"] * 5, n)
    df = pd.DataFrame({"plan": plan, "target": target})

    result = _pipeline(df, target_column="target")

    for issue in result.issues:
        if issue.category in (
            "Encoding Needed", "Missing Values", "Feature Scaling Needed",
            "Multicollinearity", "Unusable Columns",
        ):
            assert "target" not in issue.affected_columns


def test_no_target_specified_infers_clustering():
    df = pd.DataFrame({"age": range(20), "income": range(20)})
    result = _pipeline(df, target_column=None)
    assert result.inferred_task == "clustering (no target specified)"


def test_numeric_target_with_many_values_infers_regression():
    df = pd.DataFrame({
        "age": range(50),
        "price": np.random.uniform(10, 1000, 50),  # target: many distinct values
    })
    result = _pipeline(df, target_column="price")
    assert result.inferred_task == "regression"


def test_categorical_target_infers_classification():
    df = pd.DataFrame({"age": range(50), "plan": ["free", "pro"] * 25})
    result = _pipeline(df, target_column="plan")
    assert result.inferred_task == "classification"


def test_severe_class_imbalance_flagged_as_high_severity():
    df = pd.DataFrame({
        "age": range(100),
        "target": ["majority"] * 95 + ["minority"] * 5,
    })
    result = _pipeline(df, target_column="target")
    imbalance_issues = [i for i in result.issues if i.category == "Class Imbalance"]
    assert len(imbalance_issues) == 1
    assert imbalance_issues[0].severity == "high"


def test_balanced_target_not_flagged_as_imbalanced():
    df = pd.DataFrame({
        "age": range(100),
        "target": (["a"] * 50) + (["b"] * 50),
    })
    result = _pipeline(df, target_column="target")
    categories = [i.category for i in result.issues]
    assert "Class Imbalance" not in categories


def test_target_leakage_detected_for_numeric_target():
    np.random.seed(1)
    target = np.random.uniform(0, 1000, 100)
    leaked = target * 1.0001 + np.random.normal(0, 0.1, 100)
    df = pd.DataFrame({"revenue": target, "leaked_copy": leaked})

    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)
    result = _check_target_leakage(df, eda, "revenue")

    assert result is not None
    assert "leaked_copy" in result.affected_columns


def test_target_leakage_detected_for_binary_categorical_target():
    """
    Regression test: eda.correlation_pairs only ever contains
    numeric-to-numeric correlations, so a naive leakage check relying
    solely on that matrix would silently find nothing for a categorical
    target -- the most common classification scenario. Locks in the
    fix that encodes a binary target and correlates it directly.
    """
    np.random.seed(1)
    n = 100
    is_approved = np.random.choice(["yes", "no"], n)
    target_numeric = (is_approved == "yes").astype(float)
    leaked_score = target_numeric + np.random.normal(0, 0.01, n)
    unrelated = np.random.uniform(0, 100, n)

    df = pd.DataFrame({
        "is_approved": is_approved, "leaked_score": leaked_score, "unrelated": unrelated,
    })
    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)
    result = _check_target_leakage(df, eda, "is_approved")

    assert result is not None
    assert "leaked_score" in result.affected_columns
    assert "unrelated" not in result.affected_columns


def test_target_leakage_skips_multiclass_categorical_target():
    """A >2-class categorical target can't be meaningfully correlated
    numerically -- must skip honestly rather than guess."""
    df = pd.DataFrame({
        "tier": np.random.choice(["bronze", "silver", "gold"], 100),
        "score": np.random.uniform(0, 100, 100),
    })
    profile = profile_dataset(df)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)
    result = _check_target_leakage(df, eda, "tier")

    assert result is None


def test_multicollinearity_flags_near_duplicate_numeric_columns():
    np.random.seed(4)
    base = np.random.uniform(0, 100, 100)
    near_copy = base * 1.001 + np.random.normal(0, 0.1, 100)
    df = pd.DataFrame({"a": base, "b": near_copy})

    result = _pipeline(df)
    categories = [i.category for i in result.issues]
    assert "Multicollinearity" in categories


def test_unusable_columns_flags_constant_and_high_cardinality():
    df = pd.DataFrame({
        "country": ["India"] * 100,  # constant
        "customer_id": [f"C{i}" for i in range(100)],  # high cardinality
        "age": range(100),
    })
    result = _pipeline(df)
    unusable = next(i for i in result.issues if i.category == "Unusable Columns")
    assert "country" in unusable.affected_columns
    assert "customer_id" in unusable.affected_columns


def test_invalid_target_column_name_is_ignored_gracefully():
    df = pd.DataFrame({"age": range(20)})
    result = _pipeline(df, target_column="does_not_exist")
    assert result.inferred_task == "clustering (no target specified)"


def test_readiness_score_never_goes_below_zero():
    """A dataset with every possible issue stacked should still clamp
    to 0, not go negative."""
    np.random.seed(1)
    n = 50
    df = pd.DataFrame({
        "a": [np.nan] * 10 + list(range(40)),
        "b": ["const"] * n,
        "cat": np.random.choice(["x"] * 48 + ["y"] * 2, n),
        "high_card": [f"id_{i}" for i in range(n)],
    })
    result = _pipeline(df)
    assert result.readiness_score >= 0.0
