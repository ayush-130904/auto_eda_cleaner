from typing import Any
import pandas as pd
import streamlit as st

DATASET = "dataset"
DATASET_METADATA = "dataset_metadata"
DATASET_FILENAME = "dataset_filename"

def init_session_state() -> None:
    st.session_state.setdefault(DATASET, None)
    st.session_state.setdefault(DATASET_METADATA, None)
    st.session_state.setdefault(DATASET_FILENAME, None)

def has_dataset() -> bool:
    return st.session_state.get(DATASET) is not None

def get_dataset() -> pd.DataFrame | None:
    return st.session_state.get(DATASET)