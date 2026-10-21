<<<<<<< HEAD
"""
Shared prompt-building infrastructure. Feature-specific prompts (cleaning
explanations, executive summaries, business insights, chatbot) are built
in their own phases, using these shared pieces.
"""

=======
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
from __future__ import annotations

import pandas as pd

SYSTEM_INSTRUCTION = (
    "You are a senior data analyst explaining technical data cleaning and "
    "analysis decisions to a business audience. Be clear, concise, and "
    "avoid unnecessary jargon. When you do use a technical term, briefly "
    "explain what it means in plain language."
)


def build_prompt(instruction: str, context: str) -> str:
<<<<<<< HEAD
    """Combine the shared system instruction, a feature-specific
    instruction, and context data into one final prompt string."""
=======
    """Combine a shared system instruction, a feature-specific instruction,
    and context data into one final prompt string."""
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    return f"{SYSTEM_INSTRUCTION}\n\n{instruction}\n\nContext:\n{context}"


def truncate_for_prompt(text: str, max_chars: int = 4000) -> str:
<<<<<<< HEAD
    """Cap context text length before sending it to the model. Handled
    once, centrally, rather than every feature-specific prompt builder
    needing to remember to do this itself."""
=======
    """Cap context text length before sending it to the model.

    Real datasets can produce cleaning logs or data summaries far larger
    than what's useful (or affordable) to send in a single prompt. Rather
    than let every feature-specific prompt builder handle this
    individually and risk inconsistent behavior, it's handled once, here.
    """
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
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
<<<<<<< HEAD
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
=======
    return "\n".join(lines)
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
