import pandas as pd
from pybit.unified_trading import HTTP

import config


def _client() -> HTTP:
    """Public piyasa verisi icin API key gerekmez, testnet/mainnet farketmez."""
    return HTTP(testnet=config.BYBIT_TESTNET)


def get_price_history(
    symbol: str,
    interval: str = None,
    limit: int = None,
    category: str = None,
) -> pd.DataFrame:
    """Bybit public kline API'sinden OHLCV verisi ceker. API key gerektirmez.

    Donen DataFrame, indicators.py / support_resistance.py ile ayni sekilde
    Open/High/Low/Close/Volume kolonlarini icerir (data_fetcher.py ile uyumlu).
    """
    interval = interval or config.CRYPTO_KLINE_INTERVAL
    limit = limit or config.CRYPTO_KLINE_LIMIT
    category = category or config.CRYPTO_CATEGORY

    resp = _client().get_kline(category=category, symbol=symbol, interval=interval, limit=limit)

    if resp.get("retCode") != 0:
        raise ValueError(f"{symbol} icin kline verisi alinamadi: {resp.get('retMsg')}")

    rows = resp["result"]["list"]
    if not rows:
        raise ValueError(f"{symbol} icin kline verisi bos dondu")

    df = pd.DataFrame(rows, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume", "Turnover"])
    df["Timestamp"] = pd.to_datetime(df["Timestamp"].astype("int64"), unit="ms")
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = df[col].astype(float)

    # Bybit en yeni mumu ilk siraya koyar, kronolojik (eskiden yeniye) siraya cevir
    df = df.set_index("Timestamp").sort_index()
    return df[["Open", "High", "Low", "Close", "Volume"]]


def get_latest_price(symbol: str, category: str = None) -> float:
    df = get_price_history(symbol, interval="1", limit=1, category=category)
    return float(df["Close"].iloc[-1])
