<<<<<<< HEAD
"""
Dataset loading and validation.

Responsibilities of this module, and only this module:
- Decide whether an uploaded file is acceptable (extension, size).
- Turn an uploaded file into a pandas DataFrame.
- Describe the loaded DataFrame (rows, columns, memory, dtypes).

Keeping this separate from the Streamlit page (pages/1_Upload.py) means
the loading/validation logic has no dependency on Streamlit at all —
it's plain Python, so it's trivially unit-testable (see tests/) and
reusable if we ever add a non-UI entry point (a CLI, a batch job, etc).
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Callable

import pandas as pd

# Maps file extension -> the pandas reader function to use.
# A dict dispatch table like this is the standard alternative to a long
# if/elif chain: adding a new format later is a one-line addition here,
# not a new branch buried in loading logic.
_READERS: dict[str, Callable[[io.BytesIO], pd.DataFrame]] = {
    ".csv": pd.read_csv,
=======
from __future__ import  annotations
import io 
from dataclasses import dataclass
from typing import Callable
import pandas as pd

_READERS: dict[str, Callable[[io.BytesIO], pd.DataFrame]] = {
    ".csv" : pd.read_csv,
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    ".xlsx": pd.read_excel,
    ".json": pd.read_json,
    ".parquet": pd.read_parquet,
}

SUPPORTED_EXTENSIONS = tuple(_READERS.keys())

<<<<<<< HEAD

class UnsupportedFileTypeError(ValueError):
    """Raised when the uploaded file's extension isn't one we support."""


class FileTooLargeError(ValueError):
    """Raised when the uploaded file exceeds the configured size limit."""


class EmptyDatasetError(ValueError):
    """Raised when the file parses successfully but contains zero rows."""


@dataclass(frozen=True)
class DatasetMetadata:
    """Plain-data summary of a loaded dataset, used across later phases
    (profiling, quality scoring, reports) so they don't each recompute
    the same basics."""

=======
class UnsupportedFileTypeError(ValueError):
    """Raised when the uploaded file's extension isn't one we support."""

class FileTooLargeError(ValueError):
    """Raised when the uploaded file exceeds the configured size limit."""

class EmptyDatasetError(ValueError):
    """Raised when the file parses successfully but contains zero rows."""

@dataclass(frozen=True)
class DatasetMetadata:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    filename: str
    file_size_mb: float
    n_rows: int
    n_columns: int
    memory_usage_mb: float
    column_names: list[str]
    dtype_counts: dict[str, int]

<<<<<<< HEAD

def _extension_of(filename: str) -> str:
    """Return the lowercase extension including the dot, e.g. '.csv'."""
=======
def _extension_of(filename: str) -> str:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()

<<<<<<< HEAD

def validate_file(filename: str, file_size_bytes: int, max_upload_mb: int) -> None:
    """
    Validate an upload before we attempt to parse it.

    Checking extension and size *before* calling pandas is deliberate:
    it gives fast, specific error messages ("file too large") instead
    of pandas failing deep inside a parser with a cryptic traceback.

    Raises UnsupportedFileTypeError or FileTooLargeError; returns None
    (no exception) if the file passes both checks.
    """
=======
def validate_file(filename: str, file_size_bytes: int, max_upload_mb: int) -> None:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
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

<<<<<<< HEAD

def load_dataset(file_obj: io.BytesIO, filename: str) -> pd.DataFrame:
    """
    Parse an uploaded file into a DataFrame.

    `file_obj` is expected to be a file-like object positioned at the
    start (Streamlit's UploadedFile satisfies this — it behaves like
    io.BytesIO). Assumes validate_file() has already been called; this
    function only handles *parsing*, not acceptance rules.

    Raises the underlying pandas/parser exception on malformed content
    (e.g. a .csv that isn't actually valid CSV) — we intentionally
    don't swallow that here, since the caller needs the real error to
    show the user something actionable.
    """
    extension = _extension_of(filename)
    reader = _READERS[extension]  # KeyError impossible if validate_file() ran first

=======
def load_dataset(file_obj: io.BytesIO, filename: str) -> pd.DataFrame:
    extension = _extension_of(filename)
    reader = _READERS[extension]
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    df = reader(file_obj)

    if df.shape[0] == 0:
        raise EmptyDatasetError(
            "The file parsed successfully but contains zero rows."
        )
<<<<<<< HEAD

    return df


def get_metadata(df: pd.DataFrame, filename: str, file_size_bytes: int) -> DatasetMetadata:
    """Compute a lightweight summary of a loaded dataset."""
=======
    return df

def get_metadata(df: pd.DataFrame, filename: str, file_size_bytes: int) -> DatasetMetadata:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
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
<<<<<<< HEAD
    )
=======
    )
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
