"""Shared test fixtures for the backend test suite."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_prices():
    """Generate a simple price series for testing."""
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.01, 252)
    prices = 100 * np.cumprod(1 + returns)
    return prices


@pytest.fixture
def sample_returns():
    """Generate a simple return series for testing."""
    np.random.seed(42)
    return np.random.normal(0.0005, 0.01, 252)


@pytest.fixture
def sample_returns_df():
    """Generate a multi-asset returns DataFrame."""
    np.random.seed(42)
    n = 252
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {
            "SPY": np.random.normal(0.0005, 0.012, n),
            "TLT": np.random.normal(0.0002, 0.008, n),
            "GLD": np.random.normal(0.0003, 0.010, n),
        },
        index=dates,
    )


@pytest.fixture
def sample_covariance():
    """Generate a realistic 3-asset covariance matrix."""
    return np.array(
        [
            [0.0400, 0.0060, 0.0020],
            [0.0060, 0.0225, 0.0030],
            [0.0020, 0.0030, 0.0100],
        ]
    )


@pytest.fixture
def sample_weights():
    """Standard equal-weight portfolio for 3 assets."""
    return np.array([1 / 3, 1 / 3, 1 / 3])


@pytest.fixture
def sample_tickers():
    """Standard ticker list."""
    return ["SPY", "TLT", "GLD"]
