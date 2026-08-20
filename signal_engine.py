from dataclasses import dataclass, field

import pandas as pd

import config


@dataclass
class Signal:
    symbol: str
    action: str  # "BUY", "SELL", "WATCH"
    reason: str
    price: float
    news: list = field(default_factory=list)


def evaluate(
    symbol: str,
    df: pd.DataFrame,
    sr_levels: dict,
    news: list | None = None,
    proximity_pct: float = config.SR_PROXIMITY_PCT,
    rsi_oversold: float = config.RSI_OVERSOLD,
    rsi_overbought: float = config.RSI_OVERBOUGHT,
) -> "Signal | None":
    """Indikator + destek/direnc kurallarina gore bir sinyal uretir.

    Bu ornek kural seti baslangic amaclidir; gercek stratejine gore
    degistirmelisin. Su an haber verisi sadece sinyalin baglamina eklenir,
    kural motorunu tetiklemez.
    """
    latest = df.iloc[-1]
    price = latest["Close"]
    rsi = latest["RSI"]
    news = news or []

    if pd.isna(rsi):
        return None

    near_support = any(
        s > 0 and abs(price - s) / s * 100 < proximity_pct for s in sr_levels.get("support", [])
    )
    near_resistance = any(
        r > 0 and abs(price - r) / r * 100 < proximity_pct for r in sr_levels.get("resistance", [])
    )

    if rsi < rsi_oversold and near_support:
        return Signal(symbol, "BUY", f"RSI {rsi:.1f} (asiri satim) + destek seviyesine yakin", price, news)
    if rsi > rsi_overbought and near_resistance:
        return Signal(symbol, "SELL", f"RSI {rsi:.1f} (asiri alim) + direnc seviyesine yakin", price, news)
    if near_support:
        return Signal(symbol, "WATCH", f"Fiyat destek seviyesine yakin (RSI {rsi:.1f})", price, news)
    if near_resistance:
        return Signal(symbol, "WATCH", f"Fiyat direnc seviyesine yakin (RSI {rsi:.1f})", price, news)
    return None
