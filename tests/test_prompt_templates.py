"""
Unit tests for modules/ai/prompt_templates.py.
"""

import pandas as pd
import pytest

from modules.ai.prompt_templates import (
    SYSTEM_INSTRUCTION,
    build_prompt,
    dataframe_sample_to_text,
    truncate_for_prompt,
)


def test_build_prompt_includes_system_instruction_and_context():
    result = build_prompt("Explain this decision.", "median was used")
    assert SYSTEM_INSTRUCTION in result
    assert "Explain this decision." in result
    assert "median was used" in result


def test_truncate_leaves_short_text_unchanged():
    text = "short text"
    assert truncate_for_prompt(text, max_chars=100) == text


def test_truncate_cuts_long_text_and_notes_how_much_was_removed():
    text = "x" * 5000
    result = truncate_for_prompt(text, max_chars=100)
    assert len(result) < len(text)
    assert result.startswith("x" * 100)
    assert "truncated" in result
    assert "4900" in result  # 5000 - 100 characters removed


def test_dataframe_sample_to_text_includes_columns_and_shape():
    df = pd.DataFrame({"age": [25, 30, 35], "plan": ["free", "pro", "free"]})
    result = dataframe_sample_to_text(df)
    assert "age" in result and "plan" in result
    assert "3 rows x 2 columns" in result


def test_dataframe_sample_to_text_respects_n_rows():
    df = pd.DataFrame({"a": range(20)})
    result = dataframe_sample_to_text(df, n_rows=3)
    # only the first 3 values should appear in the sample section
    assert "0" in result and "1" in result and "2" in result
