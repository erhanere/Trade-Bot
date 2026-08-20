import numpy as np
import pandas as pd
import pytest

from indicators import add_indicators, bollinger_bands, macd, rsi, sma


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
    for col in [
        "RSI", "MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9", "SMA50", "SMA200",
        "BB_upper", "BB_middle", "BB_lower",
    ]:
        assert col in result.columns
    assert not result["SMA200"].isna().all()


def test_bollinger_bands_middle_matches_sma():
    close = pd.Series(100 + np.cumsum(np.random.default_rng(3).normal(0, 1, 60)))
    result = bollinger_bands(close, length=20, std_mult=2.0)
    expected_middle = close.rolling(window=20, min_periods=20).mean()
    pd.testing.assert_series_equal(result["BB_middle"], expected_middle, check_names=False)


def test_bollinger_bands_upper_above_lower():
    close = pd.Series(100 + np.cumsum(np.random.default_rng(4).normal(0, 1, 60)))
    result = bollinger_bands(close, length=20, std_mult=2.0).dropna()
    assert (result["BB_upper"] > result["BB_lower"]).all()


def test_bollinger_bands_are_symmetric_around_middle():
    close = pd.Series(100 + np.cumsum(np.random.default_rng(5).normal(0, 1, 60)))
    result = bollinger_bands(close, length=20, std_mult=2.0).dropna()
    upper_gap = result["BB_upper"] - result["BB_middle"]
    lower_gap = result["BB_middle"] - result["BB_lower"]
    pd.testing.assert_series_equal(upper_gap, lower_gap, check_names=False)


def test_bollinger_bands_widen_with_higher_std_mult():
    close = pd.Series(100 + np.cumsum(np.random.default_rng(6).normal(0, 1, 60)))
    narrow = bollinger_bands(close, length=20, std_mult=1.0).dropna()
    wide = bollinger_bands(close, length=20, std_mult=3.0).dropna()
    assert (wide["BB_upper"] > narrow["BB_upper"]).all()
    assert (wide["BB_lower"] < narrow["BB_lower"]).all()
