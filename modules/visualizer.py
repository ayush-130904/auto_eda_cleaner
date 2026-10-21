<<<<<<< HEAD
"""
Chart building.

Each function builds ONE Plotly figure and returns it -- no Streamlit
dependency here at all, same separation as every other module in this
project. Pages decide which chart to show and when; this file only
knows how to build each chart type.
"""

=======
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


<<<<<<< HEAD
def build_histogram(df: pd.DataFrame, column: str) -> go.Figure:
    """Distribution of a single numeric column."""
=======
#histogram plot
def build_histogram(df: pd.DataFrame, column: str) -> go.Figure:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    fig = px.histogram(
        df,
        x=column,
        nbins=30,
        title=f"Distribution of {column}",
        color_discrete_sequence=["#4C78A8"],
    )
    fig.update_layout(
        xaxis_title=column,
        yaxis_title="Count",
        bargap=0.05,
    )
    return fig


<<<<<<< HEAD
def build_scatter(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    color_column: str | None = None,
) -> go.Figure:
    """Relationship between two numeric columns, optionally colored by a
    third (usually categorical) column."""
    both_numeric = df[x_column].dtype.kind in "if" and df[y_column].dtype.kind in "if"
=======
#scatter plot
def build_scatter(df: pd.DataFrame, x_column: str, y_column: str, color_column: str | None = None) -> go.Figure:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    fig = px.scatter(
        df,
        x=x_column,
        y=y_column,
        color=color_column,
        title=f"{y_column} vs {x_column}",
        opacity=0.6,
<<<<<<< HEAD
        trendline="ols" if both_numeric else None,
=======
        trendline="ols" if df[x_column].dtype.kind in "if" and df[y_column].dtype.kind in "if" else None,
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    )
    fig.update_layout(xaxis_title=x_column, yaxis_title=y_column)
    return fig


<<<<<<< HEAD
def build_box_plot(df: pd.DataFrame, column: str, group_by: str | None = None) -> go.Figure:
    """Five-number-summary view of a numeric column, optionally split by
    a categorical group."""
=======
#box plot
def build_box_plot(df: pd.DataFrame, column: str, group_by: str | None = None) -> go.Figure:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    fig = px.box(
        df,
        y=column,
        x=group_by,
        title=f"Box Plot of {column}" + (f" by {group_by}" if group_by else ""),
        points="outliers",
    )
    fig.update_layout(yaxis_title=column)
    return fig


<<<<<<< HEAD
def build_correlation_heatmap(correlation_matrix: pd.DataFrame) -> go.Figure:
    """Renders an existing correlation matrix (from modules.eda) as a
    heatmap. Does not recompute correlations itself."""
=======
#correlation heatmap
def build_correlation_heatmap(correlation_matrix: pd.DataFrame) -> go.Figure:
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
    fig = px.imshow(
        correlation_matrix,
        text_auto=".2f",
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1,
        title="Correlation Heatmap",
    )
    fig.update_layout(xaxis_title="", yaxis_title="")
<<<<<<< HEAD
    return fig
=======
    return fig
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
