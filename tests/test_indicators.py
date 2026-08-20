import numpy as np
import pandas as pd
import pytest

from indicators import add_indicators, macd, rsi, sma


def test_rsi_is_100_for_strictly_increasing_series():
    close = pd.Series(np.arange(1, 31, dtype=float))
    result = rsi(close, length=14)
    assert result.iloc[-1] == pytest.approx(100)


def test_rsi_is_0_for_strictly_decreasing_series():
    close = pd.Series(np.arange(30, 0, -1, dtype=float))
    result = rsi(close, length=14)
    assert result.iloc[-1] == pytest.approx(0)


def test_rsi_stays_within_bounds():
    rng = np.random.default_rng(42)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 200)))
    result = rsi(close, length=14).dropna()
    assert (result >= 0).all()
    assert (result <= 100).all()


def test_sma_matches_pandas_rolling_mean():
    close = pd.Series(np.arange(1, 21, dtype=float))
    result = sma(close, length=5)
    expected = close.rolling(window=5).mean()
    pd.testing.assert_series_equal(result, expected)


def test_macd_line_equals_ema_difference():
    close = pd.Series(100 + np.cumsum(np.random.default_rng(1).normal(0, 1, 60)))
    result = macd(close, fast=12, slow=26, signal=9)
    ema_fast = close.ewm(span=12, adjust=False).mean()
    ema_slow = close.ewm(span=26, adjust=False).mean()
    expected_line = ema_fast - ema_slow
    pd.testing.assert_series_equal(result["MACD_12_26_9"], expected_line, check_names=False)


def test_add_indicators_adds_expected_columns():
    close = pd.Series(100 + np.cumsum(np.random.default_rng(2).normal(0, 1, 250)))
    df = pd.DataFrame({"Close": close})
    result = add_indicators(df)
    for col in ["RSI", "MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9", "SMA50", "SMA200"]:
        assert col in result.columns
    assert not result["SMA200"].isna().all()
