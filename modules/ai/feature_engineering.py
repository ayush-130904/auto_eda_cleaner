<<<<<<< HEAD
"""
AI-generated feature engineering suggestions.

The AI path can reason about what column names likely mean semantically
(e.g. 'revenue' and 'cost' suggesting a profit-margin ratio). The
fallback (used on AI failure) is structural only -- binning,
interactions, transforms, date parts, and encoding, derived purely from
column shape and statistics, never from guessing what a column means.
"""

=======
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
from __future__ import annotations

from modules.ai.client import GeminiClient
from modules.ai.prompt_templates import build_prompt, truncate_for_prompt
from modules.eda import EDAResult
from modules.profiler import DatasetProfile

_INSTRUCTION = (
    "Below are the columns and statistical findings for a cleaned "
    "dataset. Suggest 3-5 concrete feature engineering ideas that could "
<<<<<<< HEAD
    "improve analysis or machine learning on this specific data â€” for "
=======
    "improve analysis or machine learning on this specific data — for "
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    "example: binning a numeric column into groups, a ratio between two "
    "related columns, an interaction term, or a derived feature based "
    "on column names and their likely meaning. For each suggestion, "
    "name the exact columns involved and briefly explain the reasoning. "
    "Only suggest features that plausibly fit these specific column "
<<<<<<< HEAD
    "names â€” do not invent columns that aren't listed. Format as a "
=======
    "names — do not invent columns that aren't listed. Format as a "
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    "markdown bullet list."
)


def _gather_context(profile: DatasetProfile, eda: EDAResult) -> str:
    lines = [
        f"Numeric columns: {', '.join(profile.numerical_columns) or '(none)'}",
        f"Categorical columns: {', '.join(profile.categorical_columns) or '(none)'}",
        f"Date columns: {', '.join(profile.date_columns) or '(none)'}",
        f"High-cardinality columns: {', '.join(profile.high_cardinality_columns) or '(none)'}",
    ]

    if eda.numeric_stats:
        lines.append("Numeric column ranges and shape:")
        for stat in eda.numeric_stats:
            lines.append(
                f"  - {stat.name}: min={stat.min}, max={stat.max}, "
                f"skewness={stat.skewness}"
            )

    if eda.correlation_pairs:
        lines.append("Strongest correlated pairs:")
        for pair in eda.correlation_pairs[:3]:
            lines.append(f"  - {pair.column_a} & {pair.column_b}: {pair.correlation}")

    return "\n".join(lines)


def build_feature_engineering_prompt(profile: DatasetProfile, eda: EDAResult) -> str:
    context = _gather_context(profile, eda)
    return build_prompt(_INSTRUCTION, truncate_for_prompt(context))


def _fallback_suggestions(profile: DatasetProfile, eda: EDAResult) -> str:
    """Structural suggestions derivable without understanding what a
    column actually means -- binning, interactions, transforms, date
    parts, and encoding, based purely on shape and statistics."""
    bullets = []
    col_lookup = {c.name: c for c in profile.columns}

    binning_candidates = [
        stat for stat in eda.numeric_stats
        if col_lookup.get(stat.name) and col_lookup[stat.name].unique_count > 10
    ][:2]
    for stat in binning_candidates:
        unique_count = col_lookup[stat.name].unique_count
        bullets.append(
<<<<<<< HEAD
            f"- **Bin `{stat.name}`** into groups (e.g. low/medium/high) â€” "
=======
            f"- **Bin `{stat.name}`** into groups (e.g. low/medium/high) — "
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
            f"it ranges from {stat.min} to {stat.max} with {unique_count} "
            f"distinct values, which may be easier to analyze as categories."
        )

    if eda.correlation_pairs:
        top = eda.correlation_pairs[0]
        bullets.append(
            f"- **Create an interaction feature** between `{top.column_a}` and "
<<<<<<< HEAD
            f"`{top.column_b}` (e.g. their product or ratio) â€” they already show "
=======
            f"`{top.column_b}` (e.g. their product or ratio) — they already show "
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
            f"a {top.strength} relationship ({top.correlation}), so a combined "
            f"feature may capture their joint effect more directly."
        )

    skewed = [s for s in eda.numeric_stats if abs(s.skewness) > 1][:2]
    for stat in skewed:
        bullets.append(
<<<<<<< HEAD
            f"- **Log-transform `{stat.name}`** â€” it is notably skewed "
=======
            f"- **Log-transform `{stat.name}`** — it is notably skewed "
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
            f"(skewness={stat.skewness}), and a log transform often makes "
            f"skewed distributions more suitable for linear models."
        )

    for col in profile.date_columns[:2]:
        bullets.append(
            f"- **Extract date parts from `{col}`** (year, month, day of "
<<<<<<< HEAD
            f"week) â€” raw dates aren't directly usable by most models, but "
=======
            f"week) — raw dates aren't directly usable by most models, but "
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
            f"their components often are."
        )

    for col in profile.high_cardinality_columns[:2]:
        bullets.append(
            f"- **Use frequency encoding (or group rare categories) for "
<<<<<<< HEAD
            f"`{col}`** â€” it has too many distinct values for standard "
=======
            f"`{col}`** — it has too many distinct values for standard "
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
            f"one-hot encoding to work well."
        )

    if not bullets:
        return "No structural feature engineering opportunities were identified for this dataset."

    return "\n".join(bullets)


def generate_feature_engineering_suggestions(
    client: GeminiClient, profile: DatasetProfile, eda: EDAResult
) -> str:
    prompt = build_feature_engineering_prompt(profile, eda)
    response = client.generate(prompt)

    if response.success:
        return response.text

<<<<<<< HEAD
    return _fallback_suggestions(profile, eda)
=======
    return _fallback_suggestions(profile, eda)
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
