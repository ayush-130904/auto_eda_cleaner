<<<<<<< HEAD
"""
Data quality assessment.

Turns the structural facts from modules/profiler.py into human-readable
scores: completeness, duplicate, consistency, validity, and one overall
weighted score. Depends on profiler.py's output on purpose — this is
the second stage in a one-directional pipeline: upload -> profile ->
quality -> cleaning.
"""

=======
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from modules.profiler import DatasetProfile

<<<<<<< HEAD
# Weights for the overall score. Missing data and duplicates are
# treated as more clearly "broken" than mild inconsistency or outliers,
# which are often legitimate and just need a closer look.
_COMPLETENESS_WEIGHT = 0.40
_DUPLICATE_WEIGHT = 0.25
_CONSISTENCY_WEIGHT = 0.20
_VALIDITY_WEIGHT = 0.15


@dataclass(frozen=True)
class QualityScore:
    """Data quality scores for a dataset, 0-100, higher is better."""

=======

@dataclass(frozen=True)
class QualityScore:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    completeness_score: float
    duplicate_score: float
    consistency_score: float
    validity_score: float
    overall_score: float
    missing_cell_count: int
    duplicate_row_count: int
    inconsistent_columns: list[str] = field(default_factory=list)
    outlier_columns: dict[str, int] = field(default_factory=dict)

<<<<<<< HEAD

def _is_mixed_type_column(series: pd.Series) -> bool:
    """True if a column's non-null values contain more than one Python type
    (e.g. a mostly-numeric column with a few stray text values)."""
=======
#detecting mixed-type columns (for the consistency score)
def _is_mixed_type_column(series: pd.Series) -> bool:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    non_null = series.dropna()
    if non_null.empty:
        return False
    types_seen = non_null.map(type).nunique()
    return types_seen > 1


<<<<<<< HEAD
def iqr_bounds(series: pd.Series) -> tuple[float, float] | None:
    """Return (lower_bound, upper_bound) for outlier detection via the
    standard 1.5*IQR rule, or None if bounds can't be meaningfully computed
    (too few values, or zero variance).

    Public because modules/cleaner.py needs the actual boundary values
    (not just a count) to cap outliers during treatment.
    """
=======
#detecting outliers with IQR (for the validity score)
def iqr_bounds(series: pd.Series) -> tuple[float, float] | None:
    """Return (lower_bound, upper_bound) for outlier detection via the
    standard 1.5*IQR rule, or None if bounds can't be meaningfully computed
    (too few values, or zero variance)."""
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    non_null = series.dropna()
    if len(non_null) < 4:
        return None

    q1 = non_null.quantile(0.25)
    q3 = non_null.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0:
        return None

    return (q1 - 1.5 * iqr, q3 + 1.5 * iqr)


def count_outliers_iqr(series: pd.Series) -> int:
<<<<<<< HEAD
    """Count outliers in a numeric column using the standard 1.5*IQR rule.

    Public (no leading underscore) because modules/cleaner.py also needs
    this exact logic to decide between mean/median imputation — renamed
    from a private helper once a second real caller showed up needing it,
    rather than duplicating the logic in cleaner.py.
    """
=======
    """Count outliers in a numeric column using the standard 1.5*IQR rule."""
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    bounds = iqr_bounds(series)
    if bounds is None:
        return 0

    lower_bound, upper_bound = bounds
    non_null = series.dropna()
    return int(((non_null < lower_bound) | (non_null > upper_bound)).sum())

<<<<<<< HEAD

def assess_quality(df: pd.DataFrame, profile: DatasetProfile) -> QualityScore:
    """Compute quality scores for `df`, reusing facts already gathered
    in `profile` (from modules.profiler.profile_dataset) where possible."""

    # --- Completeness ---
=======
def assess_quality(df: pd.DataFrame, profile: DatasetProfile) -> QualityScore:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    total_cells = profile.n_rows * profile.n_columns
    missing_cell_count = sum(c.missing_count for c in profile.columns)
    completeness_score = (
        100 - (missing_cell_count / total_cells * 100) if total_cells else 100.0
    )

<<<<<<< HEAD
    # --- Duplicates (reuses profiler.py's work directly) ---
    duplicate_score = 100 - profile.duplicate_pct

    # --- Consistency ---
=======
    duplicate_score = 100 - profile.duplicate_pct

>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    inconsistent_columns = [
        col for col in df.columns if _is_mixed_type_column(df[col])
    ]
    consistency_score = (
        100 - (len(inconsistent_columns) / profile.n_columns * 100)
        if profile.n_columns
        else 100.0
    )

<<<<<<< HEAD
    # --- Validity (outliers, numeric columns only) ---
=======
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    outlier_columns: dict[str, int] = {}
    for col in profile.numerical_columns:
        count = count_outliers_iqr(df[col])
        if count > 0:
            outlier_columns[col] = count

    total_numeric_cells = profile.n_rows * len(profile.numerical_columns)
    total_outliers = sum(outlier_columns.values())
    validity_score = (
        100 - (total_outliers / total_numeric_cells * 100)
        if total_numeric_cells
        else 100.0
    )

<<<<<<< HEAD
    # --- Overall weighted score ---
    overall_score = (
        completeness_score * _COMPLETENESS_WEIGHT
        + duplicate_score * _DUPLICATE_WEIGHT
        + consistency_score * _CONSISTENCY_WEIGHT
        + validity_score * _VALIDITY_WEIGHT
=======
    overall_score = (
        completeness_score * 0.40
        + duplicate_score * 0.25
        + consistency_score * 0.20
        + validity_score * 0.15
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    )
    overall_score = max(0.0, min(100.0, overall_score))

    return QualityScore(
        completeness_score=round(max(0.0, completeness_score), 2),
        duplicate_score=round(max(0.0, duplicate_score), 2),
        consistency_score=round(max(0.0, consistency_score), 2),
        validity_score=round(max(0.0, validity_score), 2),
        overall_score=round(overall_score, 2),
        missing_cell_count=missing_cell_count,
        duplicate_row_count=profile.duplicate_rows,
        inconsistent_columns=inconsistent_columns,
        outlier_columns=outlier_columns,
<<<<<<< HEAD
    )
=======
    )
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
