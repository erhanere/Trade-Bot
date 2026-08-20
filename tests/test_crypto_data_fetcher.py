import pytest

import crypto_data_fetcher


def _bybit_kline_response(rows):
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {"symbol": "BTCUSDT", "category": "linear", "list": rows},
    }


def _sample_rows(n=5, start_ts=1_700_000_000_000, step_ms=3_600_000):
    # Bybit en yeni mumu ilk siraya koyar (azalan zaman sirasi)
    rows = []
    for i in range(n):
        ts = start_ts + (n - 1 - i) * step_ms
        price = 100.0 + (n - 1 - i)
        rows.append([str(ts), str(price), str(price + 1), str(price - 1), str(price + 0.5), "10.5", "1050"])
    return rows


class FakeHTTP:
    def __init__(self, response):
        self._response = response

    def get_kline(self, category, symbol, interval, limit):
        self.last_call = {"category": category, "symbol": symbol, "interval": interval, "limit": limit}
        return self._response


def test_get_price_history_returns_chronologically_sorted_df(monkeypatch):
    rows = _sample_rows(5)
    fake = FakeHTTP(_bybit_kline_response(rows))
    monkeypatch.setattr(crypto_data_fetcher, "_client", lambda: fake)

    df = crypto_data_fetcher.get_price_history("BTCUSDT")

    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(df) == 5
    assert df.index.is_monotonic_increasing
    # En eski mum en dusuk fiyata sahip olmali (sample_rows artan fiyat verir)
    assert df["Close"].iloc[0] < df["Close"].iloc[-1]


def test_get_price_history_passes_correct_params(monkeypatch):
    fake = FakeHTTP(_bybit_kline_response(_sample_rows(3)))
    monkeypatch.setattr(crypto_data_fetcher, "_client", lambda: fake)

    crypto_data_fetcher.get_price_history("ETHUSDT", interval="15", limit=100, category="linear")

    assert fake.last_call == {"category": "linear", "symbol": "ETHUSDT", "interval": "15", "limit": 100}


def test_get_price_history_raises_on_error_response(monkeypatch):
    fake = FakeHTTP({"retCode": 10001, "retMsg": "invalid symbol", "result": {"list": []}})
    monkeypatch.setattr(crypto_data_fetcher, "_client", lambda: fake)

    with pytest.raises(ValueError):
        crypto_data_fetcher.get_price_history("BADSYM")


def test_get_price_history_raises_on_empty_list(monkeypatch):
    fake = FakeHTTP(_bybit_kline_response([]))
    monkeypatch.setattr(crypto_data_fetcher, "_client", lambda: fake)

    with pytest.raises(ValueError):
        crypto_data_fetcher.get_price_history("BTCUSDT")


def test_get_latest_price_returns_last_close(monkeypatch):
    rows = _sample_rows(5)
    fake = FakeHTTP(_bybit_kline_response(rows))
    monkeypatch.setattr(crypto_data_fetcher, "_client", lambda: fake)

    price = crypto_data_fetcher.get_latest_price("BTCUSDT")

    df = crypto_data_fetcher.get_price_history("BTCUSDT")
    assert price == df["Close"].iloc[-1]
