from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


#numerical column analysis
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


def analyze_numeric_columns(df: pd.DataFrame, numerical_columns: list[str]) -> list[NumericColumnStats]:
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


#categorical column analysis
@dataclass(frozen=True)
class CategoricalColumnStats:
    name: str
    unique_count: int
    top_value: str
    top_value_count: int
    top_value_pct: float
    value_counts: dict[str, int] = field(default_factory=dict)


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
    return stats