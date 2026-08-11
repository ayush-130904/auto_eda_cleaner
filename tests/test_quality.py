import numpy as np
import pandas as pd
import pytest

from modules.profiler import profile_dataset
from modules.quality import assess_quality

def _make_messy_dataset() -> pd.DataFrame:
    np.random.seed(42)

    n = 200
    age = list(np.random.randint(20, 60, n))
    income = list(np.random.uniform(30000, 90000, n))
    signup_source = list(np.random.choice(["web", "mobile", "referral"], n))

    age[0] = 9999      # outlier
    age[1] = -500       # outlier
    income[5] = "unknown"   # mixed type
    income[10] = "N/A"      # mixed type

    df = pd.DataFrame({"age": age, "income": income, "signup_source": signup_source})

    df.loc[50:79, "age"] = np.nan          # 30 missing values, isolated range

    df = pd.concat([df, df.iloc[100:140]], ignore_index=True)  # 40 duplicates, isolated range
    return df

def test_quality_detects_exact_duplicate_count():
    df = _make_messy_dataset()
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    assert quality.duplicate_row_count == 40


def test_quality_detects_mixed_type_column():
    ...
    assert quality.inconsistent_columns == ["income"]

def test_quality_detects_outliers_with_correct_count():
    ...
    assert quality.outlier_columns.get("age") == 2

def test_quality_scores_are_bounded_0_to_100():
    ...
    for score in (
        quality.completeness_score,
        quality.duplicate_score,
        quality.consistency_score,
        quality.validity_score,
        quality.overall_score,
    ):
        assert 0.0 <= score <= 100.0

def test_clean_dataset_scores_100():
    df = pd.DataFrame(
        {
            "age": np.random.randint(20, 60, 100),
            "income": np.random.uniform(30000, 90000, 100),
        }
    )
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    assert quality.overall_score == 100.0
    assert quality.inconsistent_columns == []
    assert quality.outlier_columns == {}


def test_messy_dataset_scores_meaningfully_lower_than_clean():
    messy_df = _make_messy_dataset()
    messy_profile = profile_dataset(messy_df)
    messy_quality = assess_quality(messy_df, messy_profile)

    clean_df = pd.DataFrame({...})
    clean_profile = profile_dataset(clean_df)
    clean_quality = assess_quality(clean_df, clean_profile)

    assert messy_quality.overall_score < clean_quality.overall_score

def test_quality_handles_empty_dataframe_without_crashing():
    df = pd.DataFrame({"a": [], "b": []})
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    assert quality.overall_score == 100.0