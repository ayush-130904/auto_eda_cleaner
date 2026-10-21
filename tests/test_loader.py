"""
Unit tests for modules/loader.py.

These run with plain pytest — no Streamlit runtime needed, because
loader.py has zero Streamlit imports. That separation is the whole
point of keeping loading logic out of the page file.
"""

import io

import pandas as pd
import pytest

from modules.loader import (
    EmptyDatasetError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    get_metadata,
    load_dataset,
    validate_file,
)


def _csv_bytes(text: str) -> io.BytesIO:
    return io.BytesIO(text.encode("utf-8"))


def test_validate_file_accepts_csv_under_limit():
    # Should not raise.
    validate_file("data.csv", file_size_bytes=1_000, max_upload_mb=50)


def test_validate_file_rejects_unsupported_extension():
    with pytest.raises(UnsupportedFileTypeError):
        validate_file("data.txt", file_size_bytes=1_000, max_upload_mb=50)


def test_validate_file_rejects_oversized_file():
    ten_mb = 10 * 1024 * 1024
    with pytest.raises(FileTooLargeError):
        validate_file("data.csv", file_size_bytes=ten_mb, max_upload_mb=5)


def test_load_dataset_parses_valid_csv():
    buf = _csv_bytes("name,age\nAyush,22\nPriya,24\n")
    df = load_dataset(buf, "people.csv")
    assert list(df.columns) == ["name", "age"]
    assert df.shape == (2, 2)


def test_load_dataset_raises_on_empty_csv():
    # Header only, zero data rows.
    buf = _csv_bytes("name,age\n")
    with pytest.raises(EmptyDatasetError):
        load_dataset(buf, "empty.csv")


def test_get_metadata_reports_correct_shape():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    metadata = get_metadata(df, "sample.csv", file_size_bytes=200)
    assert metadata.n_rows == 3
    assert metadata.n_columns == 2
    assert metadata.column_names == ["a", "b"]
    assert metadata.filename == "sample.csv"
