"""
Shared prompt-building infrastructure. Feature-specific prompts (cleaning
explanations, executive summaries, business insights, chatbot) are built
in their own phases, using these shared pieces.
"""

from __future__ import annotations

import pandas as pd

SYSTEM_INSTRUCTION = (
    "You are a senior data analyst explaining technical data cleaning and "
    "analysis decisions to a business audience. Be clear, concise, and "
    "avoid unnecessary jargon. When you do use a technical term, briefly "
    "explain what it means in plain language."
)


def build_prompt(instruction: str, context: str) -> str:
    """Combine the shared system instruction, a feature-specific
    instruction, and context data into one final prompt string."""
    return f"{SYSTEM_INSTRUCTION}\n\n{instruction}\n\nContext:\n{context}"


def truncate_for_prompt(text: str, max_chars: int = 4000) -> str:
    """Cap context text length before sending it to the model. Handled
    once, centrally, rather than every feature-specific prompt builder
    needing to remember to do this itself."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... (truncated, {len(text) - max_chars} more characters)"


def dataframe_sample_to_text(df: pd.DataFrame, n_rows: int = 5) -> str:
    """A compact text representation of a DataFrame's shape and a few
    sample rows, safe to embed directly in a prompt."""
    lines = [
        f"Columns: {', '.join(df.columns)}",
        f"Shape: {df.shape[0]} rows x {df.shape[1]} columns",
        "Sample rows:",
        df.head(n_rows).to_string(index=False),
    ]
    return "\n".join(lines)


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Return the correctly pluralized word for `count`. Shared here
    because grammar text like 'N row(s)' shows up across multiple AI
    modules (executive_summary.py, chatbot.py) -- found the same bug
    (hardcoded plural producing '1 columns') independently in two
    places before consolidating the fix into one function."""
    if count == 1:
        return singular
    return plural if plural is not None else f"{singular}s"
