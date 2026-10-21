"""Unit tests for modules/ai/ml_recommendation.py."""

import numpy as np
import pandas as pd
import pytest

from modules.ai.client import AIResponse
from modules.ai.ml_recommendation import _fallback_recommendations, generate_ml_recommendations
from modules.eda import run_eda
from modules.ml_readiness import assess_ml_readiness
from modules.profiler import profile_dataset
from modules.quality import assess_quality


class _StubClient:
    def __init__(self, response):
        self._response = response

    def generate(self, prompt, max_retries=3):
        return self._response


def _readiness(df, target_column=None):
    profile = profile_dataset(df)
    quality = assess_quality(df, profile)
    eda = run_eda(df, profile.numerical_columns, profile.categorical_columns)
    return profile, eda, assess_ml_readiness(df, profile, quality, eda, target_column=target_column)


def test_fallback_avoids_accuracy_when_imbalance_detected():
    np.random.seed(2)
    n = 300
    df = pd.DataFrame({
        "age": np.random.uniform(20, 60, n),
        "target": np.random.choice(["churned"] * 95 + ["stayed"] * 5, n),
    })
    _, _, readiness = _readiness(df, target_column="target")
    result = _fallback_recommendations(readiness)
    assert "not accuracy alone" in result


def test_fallback_recommends_clustering_without_target():
    df = pd.DataFrame({"age": range(50), "income": range(50)})
    _, _, readiness = _readiness(df, target_column=None)
    result = _fallback_recommendations(readiness)
    assert "K-Means" in result


def test_fallback_recommends_regression_algorithms():
    df = pd.DataFrame({"age": range(50), "price": np.random.uniform(10, 1000, 50)})
    _, _, readiness = _readiness(df, target_column="price")
    result = _fallback_recommendations(readiness)
    assert "Linear Regression" in result
    assert "RMSE" in result


def test_generate_returns_ai_text_on_success():
    df = pd.DataFrame({"age": range(50)})
    profile, eda, readiness = _readiness(df)
    client = _StubClient(AIResponse(success=True, text="AI recommendation", attempts=1))
    result = generate_ml_recommendations(client, profile, eda, readiness)
    assert result == "AI recommendation"


def test_generate_falls_back_on_failure():
    df = pd.DataFrame({"age": range(50), "income": range(50)})
    profile, eda, readiness = _readiness(df)
    client = _StubClient(AIResponse(success=False, text="", error="down", attempts=3))
    result = generate_ml_recommendations(client, profile, eda, readiness)
    assert "K-Means" in result
