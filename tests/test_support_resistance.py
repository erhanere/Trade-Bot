import pandas as pd

from support_resistance import find_support_resistance


def _zigzag_frame():
    # Belirgin pivot tepe/dip noktalari olan bir seri: 100 -> 120 -> 90 -> 130 -> 95 -> 110
    closes = [100, 105, 110, 115, 120, 115, 110, 105, 100, 95, 90, 95, 100,
              110, 120, 130, 125, 120, 115, 110, 105, 100, 95, 95, 95, 100, 105, 110]
    data = {
        "Open": closes,
        "High": [c + 1 for c in closes],
        "Low": [c - 1 for c in closes],
        "Close": closes,
        "Volume": [1000] * len(closes),
    }
    return pd.DataFrame(data)


def test_returns_empty_when_not_enough_data():
    df = pd.DataFrame({"High": [1, 2, 3], "Low": [1, 2, 3], "Close": [1, 2, 3]})
    result = find_support_resistance(df, window=5)
    assert result == {"resistance": [], "support": []}


def test_finds_pivot_levels():
    df = _zigzag_frame()
    result = find_support_resistance(df, window=3)
    assert isinstance(result["resistance"], list)
    assert isinstance(result["support"], list)


def test_resistance_levels_are_above_current_price():
    df = _zigzag_frame()
    current_price = df["Close"].iloc[-1]
    result = find_support_resistance(df, window=3)
    assert all(level >= current_price for level in result["resistance"])


def test_support_levels_are_below_current_price():
    df = _zigzag_frame()
    current_price = df["Close"].iloc[-1]
    result = find_support_resistance(df, window=3)
    assert all(level <= current_price for level in result["support"])


def test_resistance_sorted_nearest_first():
    df = _zigzag_frame()
    result = find_support_resistance(df, window=3)
    levels = result["resistance"]
    assert levels == sorted(levels)


def test_support_sorted_nearest_first():
    df = _zigzag_frame()
    result = find_support_resistance(df, window=3)
    levels = result["support"]
    assert levels == sorted(levels, reverse=True)


def test_respects_num_levels_limit():
    df = _zigzag_frame()
    result = find_support_resistance(df, window=2, num_levels=1)
    assert len(result["resistance"]) <= 1
    assert len(result["support"]) <= 1
