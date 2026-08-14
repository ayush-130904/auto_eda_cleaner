import pandas as pd
import streamlit as st

from modules.eda import run_eda
from modules.profiler import profile_dataset
from utils.config import load_settings
from utils.logger import get_logger
from utils.session import get_active_dataset, has_dataset, init_session_state

settings = load_settings()
logger = get_logger("pages.eda", settings.logs_dir, settings.log_level)
init_session_state()

st.title("Exploratory Data Analysis")

if not has_dataset():
    st.info("Upload a dataset first on the **Upload** page.")
    st.stop()

df = get_active_dataset()

st.caption(
    "Analyzing the cleaned dataset." if "cleaned_dataset" in st.session_state
    and st.session_state["cleaned_dataset"] is not None
    else "Analyzing the original uploaded dataset (no cleaning has been run yet)."
)

#running the pipeline, cached
@st.cache_data(show_spinner="Running exploratory analysis...")
def _cached_eda(data: pd.DataFrame):
    profile = profile_dataset(data)
    return run_eda(data, profile.numerical_columns, profile.categorical_columns)


eda = _cached_eda(df)

logger.info(
    "EDA complete | numeric_cols=%d categorical_cols=%d correlations=%d",
    len(eda.numeric_stats),
    len(eda.categorical_stats),
    len(eda.correlation_pairs),
)

#the numeric statistics table
if eda.numeric_stats:
    st.subheader("Numeric Column Statistics")

    numeric_rows = [
        {
            "Column": s.name,
            "Mean": s.mean,
            "Median": s.median,
            "Std Dev": s.std,
            "Min": s.min,
            "Max": s.max,
            "Q1": s.q1,
            "Q3": s.q3,
            "Skewness": s.skewness,
        }
        for s in eda.numeric_stats
    ]
    st.dataframe(pd.DataFrame(numeric_rows), width="stretch", hide_index=True)
else:
    st.info("No numeric columns found in this dataset.")


#categorical breakdown, with a nested expander per column
if eda.categorical_stats:
    st.subheader("Categorical Column Breakdown")

    for s in eda.categorical_stats:
        with st.expander(f"{s.name} — {s.unique_count} unique values"):
            st.write(f"Most common: **{s.top_value}** ({s.top_value_pct}% of rows)")
            counts_df = pd.DataFrame(
                {"Value": list(s.value_counts.keys()), "Count": list(s.value_counts.values())}
            )
            st.bar_chart(counts_df.set_index("Value"))
else:
    st.info("No categorical columns found in this dataset.")


#correlation results
st.subheader("Correlation Analysis")

if eda.correlation_pairs:
    st.write("Notable relationships between numeric columns (|correlation| ≥ 0.5):")

    corr_rows = [
        {
            "Column A": p.column_a,
            "Column B": p.column_b,
            "Correlation": p.correlation,
            "Strength": p.strength,
        }
        for p in eda.correlation_pairs
    ]
    st.dataframe(pd.DataFrame(corr_rows), width="stretch", hide_index=True)

elif len(eda.numeric_stats) < 2:
    st.info("Need at least 2 numeric columns to compute correlations.")

else:
    st.success("No strong correlations (≥ 0.5) found between numeric columns.")

if not eda.correlation_matrix.empty:
    with st.expander("Full correlation matrix"):
        st.dataframe(
            eda.correlation_matrix.round(2), width="stretch"
        )