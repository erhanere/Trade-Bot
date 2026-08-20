import pandas as pd

from signal_engine import evaluate


def _df_with(price: float, rsi: float) -> pd.DataFrame:
    return pd.DataFrame({"Close": [price], "RSI": [rsi]})


def test_buy_signal_when_oversold_near_support():
    df = _df_with(price=100.0, rsi=25.0)
    sr = {"support": [99.7], "resistance": [120.0]}
    signal = evaluate("AAPL", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal.action == "BUY"
    assert signal.symbol == "AAPL"
    assert signal.price == 100.0


def test_sell_signal_when_overbought_near_resistance():
    df = _df_with(price=100.0, rsi=75.0)
    sr = {"support": [80.0], "resistance": [100.3]}
    signal = evaluate("AAPL", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal.action == "SELL"


def test_watch_signal_near_support_without_oversold_rsi():
    df = _df_with(price=100.0, rsi=50.0)
    sr = {"support": [99.7], "resistance": [120.0]}
    signal = evaluate("AAPL", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal.action == "WATCH"


def test_no_signal_when_not_near_any_level():
    df = _df_with(price=100.0, rsi=50.0)
    sr = {"support": [50.0], "resistance": [200.0]}
    signal = evaluate("AAPL", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal is None


def test_no_signal_when_rsi_is_nan():
    df = _df_with(price=100.0, rsi=float("nan"))
    sr = {"support": [99.7], "resistance": [120.0]}
    signal = evaluate("AAPL", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal is None


def test_news_is_attached_to_signal():
    df = _df_with(price=100.0, rsi=25.0)
    sr = {"support": [99.7], "resistance": [120.0]}
    news = [{"headline": "Earnings beat"}]
    signal = evaluate("AAPL", df, sr, news=news, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal.news == news


def test_no_signal_with_empty_sr_levels():
    df = _df_with(price=100.0, rsi=25.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate("AAPL", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal is None
