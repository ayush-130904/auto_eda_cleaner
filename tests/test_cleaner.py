"""
Unit tests for modules/cleaner.py.
"""

import numpy as np
import pandas as pd
import pytest

from modules.cleaner import (
    CleaningLog,
    auto_clean,
    clean_string_columns,
    handle_missing_values,
    remove_duplicates,
    treat_outliers,
)


def test_remove_duplicates_drops_exact_copies_only():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    log = CleaningLog()
    result = remove_duplicates(df, log)
    assert len(result) == 2
    assert log.actions[0].rows_affected == 1


def test_remove_duplicates_logs_nothing_when_no_duplicates_exist():
    df = pd.DataFrame({"a": [1, 2, 3]})
    log = CleaningLog()
    remove_duplicates(df, log)
    assert len(log.actions) == 0


def test_string_cleaning_strips_whitespace():
    df = pd.DataFrame({"country": ["india", "india ", " india"]})
    log = CleaningLog()
    result = clean_string_columns(df, log)
    assert list(result["country"]) == ["india", "india", "india"]


def test_string_cleaning_normalizes_case_only_when_it_reduces_categories():
    """
    Regression test: this used to fail on pandas 3.x, because the check
    `series.dtype != object` no longer matches pandas' newer dedicated
    string dtype, silently skipping every string column entirely.
    """
    df = pd.DataFrame({"country": ["india", "India", "INDIA", "india "]})
    log = CleaningLog()
    result = clean_string_columns(df, log)
    assert list(result["country"].unique()) == ["india"]
    assert len(log.actions) == 2  # whitespace fix + casing fix


def test_string_cleaning_leaves_already_consistent_casing_alone():
    df = pd.DataFrame({"plan": ["free", "pro", "free", "pro"]})
    log = CleaningLog()
    clean_string_columns(df, log)
    assert len(log.actions) == 0


def test_missing_values_use_median_when_outliers_present():
    df = pd.DataFrame({"age": [25, 30, 9999, np.nan, 22, 24, 26, 28]})
    log = CleaningLog()
    result = handle_missing_values(df, log)
    assert not result["age"].isna().any()
    assert log.actions[0].method == "median imputation"


def test_missing_values_use_mode_for_categorical_columns():
    df = pd.DataFrame({"plan": ["free", "free", "pro", None]})
    log = CleaningLog()
    result = handle_missing_values(df, log)
    assert result["plan"].iloc[3] == "free"
    assert log.actions[0].method == "mode imputation"


def test_outlier_treatment_caps_without_removing_rows():
    df = pd.DataFrame({"age": [25, 30, 9999, -500, 22, 24, 26, 28]})
    log = CleaningLog()
    result = treat_outliers(df, log)
    assert len(result) == len(df)  # no rows dropped
    assert result["age"].max() < 9999
    assert result["age"].min() > -500


def test_auto_clean_fixes_all_four_problems_together():
    """
    End-to-end test with all four problems injected at once, mirroring
    the manual stress test used to find the real bugs in this phase.
    """
    np.random.seed(1)
    n = 100
    age = list(np.random.randint(20, 60, n))
    age[0] = 9999
    age[1] = -500
    country = list(np.random.choice(["india", "India", "INDIA", "india "], n))
    plan = list(np.random.choice(["free", "pro"], n))

    df = pd.DataFrame({"age": age, "country": country, "plan": plan})
    df.loc[10:19, "age"] = np.nan
    df = pd.concat([df, df.iloc[30:35]], ignore_index=True)

    cleaned_df, log = auto_clean(df)

    assert cleaned_df.duplicated().sum() == 0
    assert cleaned_df["age"].isna().sum() == 0
    assert list(cleaned_df["country"].unique()) == ["india"]
    assert cleaned_df["age"].max() < 9999
    assert cleaned_df["age"].min() > -500
    assert len(log.actions) > 0


def test_auto_clean_final_pass_catches_duplicates_created_by_imputation():
    """
    Regression test: filling two rows' missing values with the same
    median (or capping two rows to the same outlier bound) can make
    rows that were NOT originally duplicates become identical. A single
    mid-pipeline dedup pass isn't enough -- only a final pass after
    every transformation is guaranteed to catch these.
    """
    df = pd.DataFrame(
        {
            "age": [np.nan, np.nan, 30, 31, 32, 33, 34, 35],
            "plan": ["free", "free", "pro", "pro", "free", "pro", "free", "pro"],
        }
    )
    # Rows 0 and 1 differ only by their (missing) age -- once both get
    # filled with the same median, they become exact duplicates.
    cleaned_df, log = auto_clean(df)
    assert cleaned_df.duplicated().sum() == 0


def test_auto_clean_returns_untouched_data_and_empty_log_for_clean_input():
    df = pd.DataFrame({"age": [25, 30, 35], "plan": ["free", "pro", "free"]})
    cleaned_df, log = auto_clean(df)
    assert len(cleaned_df) == 3
    assert len(log.actions) == 0


def test_cleaning_log_to_dataframe_has_correct_columns_when_empty():
    log = CleaningLog()
    df = log.to_dataframe()
    assert list(df.columns) == [
        "timestamp", "column", "issue", "method",
        "reason", "rows_affected", "before_summary", "after_summary",
    ]
    assert len(df) == 0
