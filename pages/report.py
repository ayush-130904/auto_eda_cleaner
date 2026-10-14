import pandas as pd
import streamlit as st

from modules.eda import run_eda
from modules.ml_readiness import assess_ml_readiness
from modules.profiler import profile_dataset
from modules.quality import assess_quality
from modules.report_generator import generate_html_report, generate_pdf_report
from utils.config import load_settings
from utils.logger import get_logger
from utils.session import (
    get_active_dataset,
    get_business_insights,
    get_cleaning_log,
    get_executive_summary,
    get_dataset,
    has_dataset,
    init_session_state,
)

settings = load_settings()
logger = get_logger("pages.report", settings.logs_dir, settings.log_level)
init_session_state()

st.title("Report")

if not has_dataset():
    st.info("Upload a dataset first on the **Upload** page.")
    st.stop()

df = get_active_dataset()
log = get_cleaning_log()
if log is None:
    from modules.cleaner import CleaningLog
    log = CleaningLog()  # dataset was never cleaned -- an empty log is accurate


@st.cache_data(show_spinner="Preparing report data...")
def _cached_pipeline(data: pd.DataFrame):
    profile = profile_dataset(data)
    quality = assess_quality(data, profile)
    eda = run_eda(data, profile.numerical_columns, profile.categorical_columns)
    readiness = assess_ml_readiness(data, profile, quality, eda)
    return profile, quality, readiness


profile, quality, readiness = _cached_pipeline(df)

executive_summary = get_executive_summary()
business_insights = get_business_insights()

st.write(
    "This report includes your dataset's profile, quality score, cleaning "
    "log, and ML readiness assessment. If you've generated the AI "
    "Executive Summary or Business Insights on the **AI Insights** page, "
    "they'll be included automatically."
)

included = ["Overview", "Data Quality", "Cleaning Log", "ML Readiness"]
included += ["Executive Summary"] if executive_summary else []
included += ["Business Insights"] if business_insights else []
st.caption(f"Sections included: {', '.join(included)}")

filename = "dataset.csv"
metadata = st.session_state.get("dataset_filename")
if metadata:
    filename = metadata

col1, col2 = st.columns(2)

with col1:
    html_report = generate_html_report(
        profile, quality, log, filename,
        executive_summary=executive_summary,
        business_insights=business_insights,
        ml_readiness=readiness,
    )
    st.download_button(
        "Download HTML Report",
        data=html_report.encode("utf-8"),
        file_name="data_intelligence_report.html",
        mime="text/html",
        width="stretch",
    )

with col2:
    pdf_report = generate_pdf_report(
        profile, quality, log, filename,
        executive_summary=executive_summary,
        business_insights=business_insights,
        ml_readiness=readiness,
    )
    st.download_button(
        "Download PDF Report",
        data=pdf_report,
        file_name="data_intelligence_report.pdf",
        mime="application/pdf",
        width="stretch",
    )

logger.info(
    "Report prepared | html_bytes=%d pdf_bytes=%d",
    len(html_report),
    len(pdf_report),
)