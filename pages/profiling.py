import pandas as pd
import streamlit as st

from modules.profiler import profile_dataset
from utils.config import load_settings
from utils.logger import get_logger
from utils.session import get_dataset, has_dataset, init_session_state

settings = load_settings()
logger = get_logger("pages.profiling", settings.logs_dir, settings.log_level)
init_session_state()

st.title("Data Profiling")

if not has_dataset():
    st.info("Upload a dataset first on the **Upload** page.")
    st.stop()

@st.cache_data(show_spinner="Profiling dataset...")
def _cached_profile(df: pd.DataFrame):
    return profile_dataset(df)

df = get_dataset()
profile = _cached_profile(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows", f"{profile.n_rows:,}")
col2.metric("Columns", profile.n_columns)
col3.metric("Duplicate rows", f"{profile.duplicate_rows} ({profile.duplicate_pct}%)")
col4.metric("Memory usage", f"{profile.memory_usage_mb} MB")

st.subheader("Column Overview")

column_rows = [
    {
        "Column": c.name,
        "Type": c.dtype,
        "Missing": f"{c.missing_count} ({c.missing_pct}%)",
        "Unique values": c.unique_count,
        "Constant": "⚠️" if c.is_constant else "",
        "High cardinality": "⚠️" if c.is_high_cardinality else "",
    }
    for c in profile.columns
]

st.dataframe(pd.DataFrame(column_rows), use_container_width="stretch", hide_index=True)

if profile.constant_columns:
    st.warning(
        f"**Constant columns** (no useful information, consider dropping): "
        f"{', '.join(profile.constant_columns)}"
    )

if profile.high_cardinality_columns:
    st.warning(
        f"**High cardinality columns** (too many unique values to treat as categories): "
        f"{', '.join(profile.high_cardinality_columns)}"
    )

if not profile.constant_columns and not profile.high_cardinality_columns:
    st.success("No constant or high-cardinality columns detected.")