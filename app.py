"""
IntelliData AI -- application entry point and landing page.

Feature pages live under pages/ and are auto-discovered by Streamlit.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from modules.loader import get_metadata
from utils.config import load_settings
from utils.logger import get_logger
from utils.session import has_dataset, init_session_state, set_dataset

st.set_page_config(
    page_title="IntelliData AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

SAMPLE_PATH = Path(__file__).resolve().parent / "sample_data" / "messy_customers.csv"


@st.cache_resource
def get_settings():
    return load_settings()


def main() -> None:
    settings = get_settings()
    logger = get_logger("app", settings.logs_dir, settings.log_level)
    init_session_state()

    st.title("📊 IntelliData AI")
    st.caption("An AI-powered data intelligence platform: upload → clean → analyze → ask.")

    st.markdown(
        """
        Upload a raw dataset and IntelliData AI will **profile** it, **score its quality**,
        **clean it automatically** (logging every decision), run **EDA and charts**, then use
        Gemini to explain what it did, summarize findings, suggest features, assess
        **ML readiness**, and let you **chat with your data**.
        """
    )

    if not settings.gemini_api_key:
        st.info(
            "Running without a GEMINI_API_KEY: all data features work, and AI sections "
            "fall back to rule-based summaries.",
            icon="ℹ️",
        )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Try it in one click")
        if st.button("Load sample messy dataset", type="primary"):
            df = pd.read_csv(SAMPLE_PATH)
            raw = SAMPLE_PATH.stat().st_size
            set_dataset(df, get_metadata(df, SAMPLE_PATH.name, raw), SAMPLE_PATH.name)
            logger.info("Sample dataset loaded")
            st.rerun()
        if has_dataset():
            st.success("Dataset loaded — open **Profiling** in the sidebar to continue.")
    with col2:
        st.subheader("Or bring your own")
        st.write("Use the **Upload** page (CSV, Excel, JSON, Parquet — up to 50MB).")

    st.divider()
    st.markdown(
        "**Workflow:** Upload → Profiling → Quality → Cleaning → EDA → Visualizations → "
        "AI Insights → ML Readiness → Chat → Report"
    )


main()
