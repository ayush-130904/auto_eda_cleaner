from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from modules.profiler import DatasetProfile


@dataclass(frozen=True)
class QualityScore:
    completeness_score: float
    duplicate_score: float
    consistency_score: float
    validity_score: float
    overall_score: float
    missing_cell_count: int
    duplicate_row_count: int
    inconsistent_columns: list[str] = field(default_factory=list)
    outlier_columns: dict[str, int] = field(default_factory=dict)