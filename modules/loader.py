from __future__ import  annotations
import io 
from dataclasses import dataclass
from typing import Callable
import pandas as pd

_READERS: dict[str, Callable[[io.BytesIO], pd.DataFrame]] = {
    ".csv" : pd.read_csv,
    ".xlsx": pd.read_excel,
    ".json": pd.read_json,
    ".parquet": pd.read_parquet,
}

SUPPORTED_EXTENSIONS = tuple(_READERS.keys())

class UnsupportedFileTypeError(ValueError):
    """Raised when the uploaded file's extension isn't one we support."""

class FileTooLargeError(ValueError):
    """Raised when the uploaded file exceeds the configured size limit."""

class EmptyDatasetError(ValueError):
    """Raised when the file parses successfully but contains zero rows."""

@dataclass(frozen=True)
class DatasetMetadata:
    filename: str
    file_size_mb: float
    n_rows: int
    n_columns: int
    memory_usage_mb: float
    column_names: list[str]
    dtype_counts: dict[str, int]

def _extension_of(filename: str) -> str:
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()

def validate_file(filename: str, file_size_bytes: int, max_upload_mb: int) -> None:
    extension = _extension_of(filename)
    if extension not in _READERS:
        raise UnsupportedFileTypeError(
            f"'{extension or 'unknown'}' is not supported. "
            f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    size_mb = file_size_bytes / (1024 * 1024)
    if size_mb > max_upload_mb:
        raise FileTooLargeError(
            f"File is {size_mb:.1f}MB, which exceeds the {max_upload_mb}MB limit."
        )

def load_dataset(file_obj: io.BytesIO, filename: str) -> pd.DataFrame:
    extension = _extension_of(filename)
    reader = _READERS[extension]
    df = reader(file_obj)

    if df.shape[0] == 0:
        raise EmptyDatasetError(
            "The file parsed successfully but contains zero rows."
        )
    return df

def get_metadata(df: pd.DataFrame, filename: str, file_size_bytes: int) -> DatasetMetadata:
    dtype_counts: dict[str, int] = {}
    for dtype in df.dtypes:
        key = str(dtype)
        dtype_counts[key] = dtype_counts.get(key, 0) + 1

    return DatasetMetadata(
        filename=filename,
        file_size_mb=round(file_size_bytes / (1024 * 1024), 3),
        n_rows=df.shape[0],
        n_columns=df.shape[1],
        memory_usage_mb=round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3),
        column_names=list(df.columns),
        dtype_counts=dtype_counts,
    )