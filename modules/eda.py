<<<<<<< HEAD
"""
Exploratory data analysis.

Produces per-column statistics (numeric and categorical) and pairwise
correlations. Takes numerical_columns/categorical_columns as parameters
rather than re-deriving them -- modules/profiler.py already did that
classification in Phase 3, so every later module reuses it.
"""

=======
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


<<<<<<< HEAD
=======
#numerical column analysis
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
@dataclass(frozen=True)
class NumericColumnStats:
    name: str
    mean: float
    median: float
    std: float
    min: float
    max: float
    q1: float
    q3: float
    skewness: float


<<<<<<< HEAD
@dataclass(frozen=True)
class CategoricalColumnStats:
    name: str
    unique_count: int
    top_value: str
    top_value_count: int
    top_value_pct: float
    value_counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class CorrelationPair:
    column_a: str
    column_b: str
    correlation: float
    strength: str


@dataclass(frozen=True)
class EDAResult:
    numeric_stats: list[NumericColumnStats]
    categorical_stats: list[CategoricalColumnStats]
    correlation_matrix: pd.DataFrame
    correlation_pairs: list[CorrelationPair]


def analyze_numeric_columns(
    df: pd.DataFrame, numerical_columns: list[str]
) -> list[NumericColumnStats]:
=======
def analyze_numeric_columns(df: pd.DataFrame, numerical_columns: list[str]) -> list[NumericColumnStats]:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    stats = []
    for col in numerical_columns:
        series = df[col].dropna()
        if series.empty:
            continue

        stats.append(
            NumericColumnStats(
                name=col,
                mean=round(float(series.mean()), 3),
                median=round(float(series.median()), 3),
                std=round(float(series.std()), 3),
                min=round(float(series.min()), 3),
                max=round(float(series.max()), 3),
                q1=round(float(series.quantile(0.25)), 3),
                q3=round(float(series.quantile(0.75)), 3),
                skewness=round(float(series.skew()), 3),
            )
        )
    return stats


<<<<<<< HEAD
=======
#categorical column analysis
@dataclass(frozen=True)
class CategoricalColumnStats:
    name: str
    unique_count: int
    top_value: str
    top_value_count: int
    top_value_pct: float
    value_counts: dict[str, int] = field(default_factory=dict)


>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
def analyze_categorical_columns(
    df: pd.DataFrame, categorical_columns: list[str], top_n: int = 10
) -> list[CategoricalColumnStats]:
    stats = []
    for col in categorical_columns:
        series = df[col].dropna()
        if series.empty:
            continue

        counts = series.value_counts().head(top_n)
        total = len(series)
        top_value = str(counts.index[0])
        top_value_count = int(counts.iloc[0])

        stats.append(
            CategoricalColumnStats(
                name=col,
                unique_count=int(series.nunique()),
                top_value=top_value,
                top_value_count=top_value_count,
                top_value_pct=round(top_value_count / total * 100, 2),
                value_counts={str(k): int(v) for k, v in counts.items()},
            )
        )
<<<<<<< HEAD
    return stats


def _strength_label(r: float) -> str:
    abs_r = abs(r)
    direction = "positive" if r > 0 else "negative"
    if abs_r >= 0.8:
        return f"very strong {direction}"
    if abs_r >= 0.6:
        return f"strong {direction}"
    return f"moderate {direction}"


def analyze_correlations(
    df: pd.DataFrame, numerical_columns: list[str], threshold: float = 0.5
) -> tuple[pd.DataFrame, list[CorrelationPair]]:
    if len(numerical_columns) < 2:
        return pd.DataFrame(), []

    corr_matrix = df[numerical_columns].corr()

    pairs = []
    seen = set()
    for col_a in numerical_columns:
        for col_b in numerical_columns:
            if col_a == col_b:
                continue
            key = frozenset({col_a, col_b})
            if key in seen:
                continue
            seen.add(key)

            corr_value = corr_matrix.loc[col_a, col_b]
            if pd.isna(corr_value) or abs(corr_value) < threshold:
                continue

            pairs.append(
                CorrelationPair(
                    column_a=col_a,
                    column_b=col_b,
                    correlation=round(float(corr_value), 3),
                    strength=_strength_label(corr_value),
                )
            )

    pairs.sort(key=lambda p: abs(p.correlation), reverse=True)
    return corr_matrix, pairs


def run_eda(
    df: pd.DataFrame,
    numerical_columns: list[str],
    categorical_columns: list[str],
) -> EDAResult:
    numeric_stats = analyze_numeric_columns(df, numerical_columns)
    categorical_stats = analyze_categorical_columns(df, categorical_columns)
    correlation_matrix, correlation_pairs = analyze_correlations(df, numerical_columns)

    return EDAResult(
        numeric_stats=numeric_stats,
        categorical_stats=categorical_stats,
        correlation_matrix=correlation_matrix,
        correlation_pairs=correlation_pairs,
    )
=======
    return stats
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
