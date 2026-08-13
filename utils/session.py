from typing import Any
import pandas as pd
import streamlit as st

DATASET = "dataset"
DATASET_METADATA = "dataset_metadata"
DATASET_FILENAME = "dataset_filename"
CLEANED_DATASET = "cleaned_dataset"
CLEANING_LOG = "cleaning_log"

def init_session_state() -> None:
    st.session_state.setdefault(DATASET, None)
    st.session_state.setdefault(DATASET_METADATA, None)
    st.session_state.setdefault(DATASET_FILENAME, None)
    st.session_state.setdefault(CLEANED_DATASET, None)
    st.session_state.setdefault(CLEANING_LOG, None)

def has_dataset() -> bool:
    return st.session_state.get(DATASET) is not None

def get_dataset() -> pd.DataFrame | None:
    return st.session_state.get(DATASET)

def set_cleaned_dataset(df: pd.DataFrame, log: Any) -> None:
    st.session_state[CLEANED_DATASET] = df
    st.session_state[CLEANING_LOG] = log


def has_cleaned_dataset() -> bool:
    return st.session_state.get(CLEANED_DATASET) is not None


def get_active_dataset() -> pd.DataFrame | None:
    """Returns the cleaned dataset if cleaning has run, otherwise the
    original upload. Every phase from here on (EDA, visualization, ML)
    should call this instead of get_dataset(), so they automatically
    work on cleaned data once it exists, without each page needing to
    know or check whether cleaning has happened yet."""
    if has_cleaned_dataset():
        return st.session_state.get(CLEANED_DATASET)
    return get_dataset()


def get_cleaning_log() -> Any:
    return st.session_state.get(CLEANING_LOG)

