import pandas as pd
import streamlit as st

from modules.eda import run_eda
from modules.profiler import profile_dataset
from modules.visualizer import (
    build_box_plot,
    build_correlation_heatmap,
    build_histogram,
    build_scatter,
)
from utils.config import load_settings
from utils.logger import get_logger
from utils.session import get_active_dataset, has_dataset, init_session_state

settings = load_settings()
logger = get_logger("pages.visualizations", settings.logs_dir, settings.log_level)
init_session_state()

st.title("Visualization Dashboard")

if not has_dataset():
    st.info("Upload a dataset first on the **Upload** page.")
    st.stop()

df = get_active_dataset()


@st.cache_data(show_spinner="Preparing dashboard...")
def _cached_profile(data: pd.DataFrame):
    return profile_dataset(data)


profile = _cached_profile(df)
numeric_cols = profile.numerical_columns
categorical_cols = profile.categorical_columns

# --- Histogram ---
st.subheader("Distribution")

if numeric_cols:
    selected_col = st.selectbox("Choose a numeric column", numeric_cols, key="hist_col")
    fig = build_histogram(df, selected_col)
    st.plotly_chart(fig, width="stretch")
else:
    st.info("No numeric columns available for a histogram.")

# --- Scatter ---
st.subheader("Relationships Between Columns")

if len(numeric_cols) >= 2:
    col1, col2, col3 = st.columns(3)
    x_col = col1.selectbox("X-axis", numeric_cols, key="scatter_x")
    y_col = col2.selectbox(
        "Y-axis", numeric_cols, index=min(1, len(numeric_cols) - 1), key="scatter_y"
    )
    color_options = ["(none)"] + categorical_cols
    color_col = col3.selectbox("Color by", color_options, key="scatter_color")

    fig = build_scatter(
        df, x_col, y_col, color_column=None if color_col == "(none)" else color_col
    )
    st.plotly_chart(fig, width="stretch")
else:
    st.info("Need at least 2 numeric columns for a scatter plot.")

# --- Box plot ---
st.subheader("Outlier View (Box Plot)")

if numeric_cols:
    col1, col2 = st.columns(2)
    box_col = col1.selectbox("Numeric column", numeric_cols, key="box_col")
    group_options = ["(none)"] + categorical_cols
    group_col = col2.selectbox("Group by", group_options, key="box_group")

    fig = build_box_plot(
        df, box_col, group_by=None if group_col == "(none)" else group_col
    )
    st.plotly_chart(fig, width="stretch")
else:
    st.info("No numeric columns available for a box plot.")

# --- Correlation heatmap ---
st.subheader("Correlation Heatmap")

if len(numeric_cols) >= 2:
    @st.cache_data(show_spinner="Computing correlations...")
    def _cached_eda(data: pd.DataFrame):
        return run_eda(data, numeric_cols, categorical_cols)

    eda = _cached_eda(df)
    fig = build_correlation_heatmap(eda.correlation_matrix)
    st.plotly_chart(fig, width="stretch")
else:
    st.info("Need at least 2 numeric columns for a correlation heatmap.")

logger.info(
    "Visualization dashboard rendered | numeric_cols=%d categorical_cols=%d",
    len(numeric_cols),
    len(categorical_cols),
)