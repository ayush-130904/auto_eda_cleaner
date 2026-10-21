"""Unit tests for modules/report_generator.py (HTML and PDF)."""

import numpy as np
import pandas as pd
import pytest
from pypdf import PdfReader
import io

from modules.cleaner import auto_clean
from modules.ml_readiness import assess_ml_readiness
from modules.eda import run_eda
from modules.profiler import profile_dataset
from modules.quality import assess_quality
from modules.report_generator import generate_html_report, generate_pdf_report


def _make_report_inputs():
    np.random.seed(1)
    n = 100
    age = list(np.random.randint(20, 60, n))
    age[0] = 9999
    income = np.random.uniform(30000, 90000, n)
    df = pd.DataFrame({"age": age, "income": income, "plan": ["free", "pro"] * 50})
    df.loc[5:14, "age"] = np.nan

    cleaned_df, log = auto_clean(df)
    profile = profile_dataset(cleaned_df)
    quality = assess_quality(cleaned_df, profile)
    eda = run_eda(cleaned_df, profile.numerical_columns, profile.categorical_columns)
    readiness = assess_ml_readiness(cleaned_df, profile, quality, eda)
    return profile, quality, log, readiness


def test_html_report_is_valid_and_contains_real_data():
    profile, quality, log, readiness = _make_report_inputs()
    html = generate_html_report(profile, quality, log, "test.csv", ml_readiness=readiness)

    assert html.startswith("<!DOCTYPE html>")
    assert str(profile.n_rows) in html
    assert str(quality.overall_score) in html


def test_html_report_converts_markdown_to_real_html_not_escaped():
    profile, quality, log, readiness = _make_report_inputs()
    html = generate_html_report(
        profile, quality, log, "test.csv",
        business_insights="- **age and income** are correlated.",
    )
    assert "<strong>age and income</strong>" in html
    assert "&lt;strong&gt;" not in html  # must not be double-escaped
    assert "**age and income**" not in html  # must not remain literal markdown


def test_html_report_omits_ai_sections_when_not_provided():
    profile, quality, log, _ = _make_report_inputs()
    html = generate_html_report(profile, quality, log, "test.csv")
    assert "Executive Summary" not in html
    assert "Business Insights" not in html


def test_pdf_report_is_valid_pdf_bytes():
    profile, quality, log, readiness = _make_report_inputs()
    pdf_bytes = generate_pdf_report(profile, quality, log, "test.csv", ml_readiness=readiness)

    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 500


def test_pdf_report_contains_real_data_when_extracted():
    profile, quality, log, readiness = _make_report_inputs()
    pdf_bytes = generate_pdf_report(
        profile, quality, log, "test.csv",
        executive_summary="This is a test summary sentence.",
        ml_readiness=readiness,
    )

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() for page in reader.pages)

    assert str(profile.n_rows) in text
    assert "This is a test summary sentence." in text
    assert "ML Readiness" in text


def test_pdf_report_bold_markdown_does_not_leave_literal_asterisks():
    profile, quality, log, _ = _make_report_inputs()
    pdf_bytes = generate_pdf_report(
        profile, quality, log, "test.csv",
        business_insights="- **age** is important.",
    )
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() for page in reader.pages)

    assert "**age**" not in text
    assert "age" in text


def test_pdf_report_handles_minimal_data_without_crashing():
    df = pd.DataFrame({"age": [25, 30, 35]})
    cleaned_df, log = auto_clean(df)
    profile = profile_dataset(cleaned_df)
    quality = assess_quality(cleaned_df, profile)

    pdf_bytes = generate_pdf_report(profile, quality, log, "minimal.csv")
    assert pdf_bytes[:4] == b"%PDF"


def test_html_and_pdf_report_both_handle_dataset_with_no_cleaning_needed():
    df = pd.DataFrame({"age": [25, 30, 35], "plan": ["free", "pro", "free"]})
    cleaned_df, log = auto_clean(df)
    assert len(log.actions) == 0  # confirm this dataset genuinely needed no cleaning
    profile = profile_dataset(cleaned_df)
    quality = assess_quality(cleaned_df, profile)

    html = generate_html_report(profile, quality, log, "clean.csv")
    assert "already clean" in html

    pdf_bytes = generate_pdf_report(profile, quality, log, "clean.csv")
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() for page in reader.pages)
    assert "already clean" in text
