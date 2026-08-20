import pandas as pd


def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    """Wilder's RSI (pandas_ta.rsi ile ayni yontem: exponential/Wilder smoothing)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()

    rs = avg_gain / avg_loss
    result = 100 - (100 / (1 + rs))
    result[avg_loss == 0] = 100
    result[(avg_gain == 0) & (avg_loss == 0)] = 50
    return result


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD line, sinyal cizgisi ve histogram. Kolon isimleri pandas_ta ile uyumlu."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return pd.DataFrame(
        {
            f"MACD_{fast}_{slow}_{signal}": macd_line,
            f"MACDs_{fast}_{slow}_{signal}": signal_line,
            f"MACDh_{fast}_{slow}_{signal}": histogram,
        }
    )


def sma(close: pd.Series, length: int) -> pd.Series:
    return close.rolling(window=length, min_periods=length).mean()


def bollinger_bands(close: pd.Series, length: int = 20, std_mult: float = 2.0) -> pd.DataFrame:
    """Bollinger Bantlari: orta bant (SMA) +/- std_mult * hareketli standart sapma."""
    middle = close.rolling(window=length, min_periods=length).mean()
    std = close.rolling(window=length, min_periods=length).std()
    return pd.DataFrame(
        {
            "BB_upper": middle + std_mult * std,
            "BB_middle": middle,
            "BB_lower": middle - std_mult * std,
        }
    )


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame'e RSI, MACD, SMA50/SMA200 ve Bollinger Bantlari kolonlarini ekler."""
    df = df.copy()
    df["RSI"] = rsi(df["Close"], length=14)
    df = pd.concat([df, macd(df["Close"])], axis=1)
    df["SMA50"] = sma(df["Close"], length=50)
    df["SMA200"] = sma(df["Close"], length=200)
    df = pd.concat([df, bollinger_bands(df["Close"], length=20, std_mult=2.0)], axis=1)
    return df
