import pandas as pd
import pytest

import data_fetcher


class FakeTicker:
    def __init__(self, symbol, frame):
        self.symbol = symbol
        self._frame = frame

    def history(self, period="1y", interval="1d"):
        return self._frame


def _sample_frame(rows=10):
    return pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(rows)],
            "High": [101.0 + i for i in range(rows)],
            "Low": [99.0 + i for i in range(rows)],
            "Close": [100.5 + i for i in range(rows)],
            "Volume": [1000 + i for i in range(rows)],
        }
    )


def test_get_price_history_returns_dataframe(monkeypatch):
    frame = _sample_frame()
    monkeypatch.setattr(data_fetcher.yf, "Ticker", lambda symbol: FakeTicker(symbol, frame))

    df = data_fetcher.get_price_history("AAPL")

    assert list(df.columns) == list(frame.columns)
    assert len(df) == len(frame)


def test_get_price_history_raises_on_empty(monkeypatch):
    monkeypatch.setattr(data_fetcher.yf, "Ticker", lambda symbol: FakeTicker(symbol, pd.DataFrame()))

    with pytest.raises(ValueError):
        data_fetcher.get_price_history("BADSYM")


def test_get_latest_price_returns_last_close(monkeypatch):
    frame = _sample_frame()
    monkeypatch.setattr(data_fetcher.yf, "Ticker", lambda symbol: FakeTicker(symbol, frame))

    price = data_fetcher.get_latest_price("AAPL")

    assert price == frame["Close"].iloc[-1]
