import pandas as pd
import streamlit as st

from modules.ai.client import GeminiClient
from modules.ai.executive_summary import generate_executive_summary
from modules.eda import run_eda
from modules.profiler import profile_dataset
from modules.quality import assess_quality
from utils.config import load_settings
from utils.logger import get_logger
from utils.session import (
    get_active_dataset,
    get_cleaning_log,
    get_executive_summary,
    has_cleaned_dataset,
    has_dataset,
    has_executive_summary,
    init_session_state,
    set_executive_summary,
)

settings = load_settings()
logger = get_logger("pages.ai_insights", settings.logs_dir, settings.log_level)
init_session_state()

st.title("AI Insights")

if not has_dataset():
    st.info("Upload a dataset first on the **Upload** page.")
    st.stop()

if not has_cleaned_dataset():
    st.info(
        "Run automatic cleaning first on the **Cleaning** page — the "
        "executive summary describes what was found and fixed, so it "
        "needs a completed cleaning pass to work from."
    )
    st.stop()

df = get_active_dataset()
log = get_cleaning_log()


@st.cache_data(show_spinner="Analyzing dataset...")
def _cached_pipeline(data: pd.DataFrame):
    profile = profile_dataset(data)
    quality = assess_quality(data, profile)
    eda = run_eda(data, profile.numerical_columns, profile.categorical_columns)
    return profile, quality, eda


profile, quality, eda = _cached_pipeline(df)

st.subheader("Executive Summary")

if not settings.gemini_api_key:
    st.info(
        "Add a GEMINI_API_KEY in your .env file to generate an AI-written "
        "executive summary."
    )
else:
    if st.button("Generate Executive Summary", type="primary"):
        with st.spinner("Writing executive summary..."):
            client = GeminiClient(
                api_key=settings.gemini_api_key, model=settings.gemini_model
            )
            summary = generate_executive_summary(client, profile, quality, log, eda)
            set_executive_summary(summary)
        logger.info("Executive summary generated | length=%d", len(summary))
        st.rerun()

    if has_executive_summary():
        st.markdown(get_executive_summary())