import pandas as pd

from signal_engine import evaluate


def _df_with(price: float, rsi: float, bb_lower: float = None, bb_upper: float = None) -> pd.DataFrame:
    return pd.DataFrame(
        {"Close": [price], "RSI": [rsi], "BB_lower": [bb_lower], "BB_upper": [bb_upper]}
    )


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


def test_buy_signal_when_oversold_and_near_bollinger_lower_band():
    # Pivot destek yok/uzak, fiyat Bollinger alt bandina yakin (henuz degmemis)
    df = _df_with(price=95.0, rsi=25.0, bb_lower=95.5, bb_upper=110.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate("BTCUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal.action == "BUY"
    assert "Bollinger alt bandina yakin" in signal.reason


def test_sell_signal_when_overbought_and_near_bollinger_upper_band():
    # Fiyat Bollinger ust bandina yakin, henuz degmemis (kullanicinin ENA senaryosu)
    df = _df_with(price=109.5, rsi=75.0, bb_lower=90.0, bb_upper=110.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate("BTCUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal.action == "SELL"
    assert "Bollinger ust bandina yakin" in signal.reason


def test_watch_signal_near_bollinger_band_without_rsi_extreme():
    df = _df_with(price=95.0, rsi=50.0, bb_lower=95.5, bb_upper=110.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate("BTCUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal.action == "WATCH"
    assert "Bollinger alt bandina yakin" in signal.reason


def test_no_signal_when_price_far_from_bollinger_bands():
    df = _df_with(price=100.0, rsi=25.0, bb_lower=90.0, bb_upper=110.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate("BTCUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal is None


def test_no_signal_when_price_touches_band_but_outside_proximity():
    # Bant henuz "yakinlik" esiginin disinda kalirsa (tam temas degil, proximity_pct'e gore)
    df = _df_with(price=95.0, rsi=25.0, bb_lower=100.0, bb_upper=110.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate("BTCUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal is None


def test_reason_mentions_both_pivot_and_bollinger_when_both_trigger():
    df = _df_with(price=95.0, rsi=25.0, bb_lower=95.3, bb_upper=110.0)
    sr = {"support": [95.2], "resistance": []}
    signal = evaluate("BTCUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal.action == "BUY"
    assert "destek seviyesine yakin" in signal.reason
    assert "Bollinger alt bandina yakin" in signal.reason


def test_watch_only_by_default_when_rsi_neutral_near_band():
    # RSI notr (50), sadece banda yakinlik var - varsayilan (require_rsi_extreme=True)
    # ile bu hala sadece WATCH (bildirim), islem tetiklenmez.
    df = _df_with(price=109.5, rsi=50.0, bb_lower=90.0, bb_upper=110.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate("ENAUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70)
    assert signal.action == "WATCH"


def test_sell_when_rsi_extreme_not_required_and_only_near_band():
    # require_rsi_extreme=False: RSI notr olsa bile bolgeye yakinlik SELL uretir
    df = _df_with(price=109.5, rsi=50.0, bb_lower=90.0, bb_upper=110.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate(
        "ENAUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70,
        require_rsi_extreme=False,
    )
    assert signal.action == "SELL"
    assert "notr" in signal.reason


def test_buy_when_rsi_extreme_not_required_and_only_near_band():
    df = _df_with(price=90.5, rsi=50.0, bb_lower=90.0, bb_upper=110.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate(
        "ENAUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70,
        require_rsi_extreme=False,
    )
    assert signal.action == "BUY"
    assert "notr" in signal.reason


def test_rsi_extreme_still_labeled_correctly_when_not_required():
    # require_rsi_extreme=False olsa da RSI gercekten asiriysa reason'da belirtilmeli
    df = _df_with(price=109.5, rsi=80.0, bb_lower=90.0, bb_upper=110.0)
    sr = {"support": [], "resistance": []}
    signal = evaluate(
        "ENAUSDT", df, sr, proximity_pct=1.0, rsi_oversold=30, rsi_overbought=70,
        require_rsi_extreme=False,
    )
    assert signal.action == "SELL"
    assert "asiri alim" in signal.reason
