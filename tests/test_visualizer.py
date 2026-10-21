"""
Unit tests for modules/visualizer.py.

Note: two assertions here were corrected after real testing revealed my
initial assumptions about Plotly's internal structure were wrong, not
the module code:
  - px.box(x=group_by) puts all categories into ONE trace (separated by
    x values), not one trace per category -- that's px.box's actual
    documented behavior, not a bug.
  - px.imshow's zmin/zmax land on fig.layout.coloraxis (as cmin/cmax),
    not on the trace itself.
"""

import numpy as np
import pandas as pd
import pytest

from modules.visualizer import (
    build_box_plot,
    build_correlation_heatmap,
    build_histogram,
    build_scatter,
)


@pytest.fixture
def sample_df():
    np.random.seed(7)
    n = 100
    age = np.random.uniform(20, 60, n)
    income = age * 500 + np.random.normal(0, 5000, n)
    plan = np.random.choice(["free", "pro"], n)
    return pd.DataFrame({"age": age, "income": income, "plan": plan})


def test_histogram_contains_all_data_points(sample_df):
    fig = build_histogram(sample_df, "age")
    assert fig.data[0].type == "histogram"
    assert len(fig.data[0].x) == 100


def test_scatter_includes_trendline_for_two_numeric_columns(sample_df):
    fig = build_scatter(sample_df, "age", "income")
    assert len(fig.data) == 2  # scatter points + OLS trendline


def test_scatter_with_color_produces_one_pair_per_category(sample_df):
    fig = build_scatter(sample_df, "age", "income", color_column="plan")
    # 2 categories (free, pro) x 2 traces each (scatter + trendline) = 4
    assert len(fig.data) == 4


def test_box_plot_ungrouped_contains_all_data_points(sample_df):
    fig = build_box_plot(sample_df, "income")
    assert fig.data[0].type == "box"
    assert len(fig.data[0].y) == 100


def test_box_plot_grouped_puts_both_categories_in_one_trace(sample_df):
    fig = build_box_plot(sample_df, "income", group_by="plan")
    assert len(fig.data) == 1
    assert set(fig.data[0].x) == {"free", "pro"}


def test_correlation_heatmap_locks_color_scale_to_minus1_plus1(sample_df):
    corr_matrix = sample_df[["age", "income"]].corr()
    fig = build_correlation_heatmap(corr_matrix)
    assert fig.data[0].type == "heatmap"
    assert fig.layout.coloraxis.cmin == -1
    assert fig.layout.coloraxis.cmax == 1


def test_titles_reflect_the_columns_being_charted(sample_df):
    assert "age" in build_histogram(sample_df, "age").layout.title.text
    assert "income" in build_box_plot(sample_df, "income").layout.title.text
    scatter_title = build_scatter(sample_df, "age", "income").layout.title.text
    assert "age" in scatter_title and "income" in scatter_title
