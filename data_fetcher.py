import pandas as pd
import yfinance as yf


def get_price_history(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Belirtilen sembol icin OHLCV verisini dondurur.

    SMA200 gibi uzun donemli indikatorler icin varsayilan period "1y" olarak
    ayarlandi (3ay yeterli veri saglamiyor).
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"{symbol} icin fiyat verisi bulunamadi")
    return df


def get_latest_price(symbol: str) -> float:
    df = get_price_history(symbol, period="1d", interval="1m")
    return float(df["Close"].iloc[-1])
