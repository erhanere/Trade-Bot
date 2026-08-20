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


def _zone_reason(pivot_hit: bool, bb_hit: bool, pivot_label: str, bb_label: str) -> str:
    parts = []
    if pivot_hit:
        parts.append(pivot_label)
    if bb_hit:
        parts.append(bb_label)
    return " + ".join(parts)


def evaluate(
    symbol: str,
    df: pd.DataFrame,
    sr_levels: dict,
    news: list | None = None,
    proximity_pct: float = config.SR_PROXIMITY_PCT,
    rsi_oversold: float = config.RSI_OVERSOLD,
    rsi_overbought: float = config.RSI_OVERBOUGHT,
) -> "Signal | None":
    """Indikator + destek/direnc + Bollinger Bant kurallarina gore bir sinyal uretir.

    "Destek/direnc bolgesi" iki sekilde tetiklenebilir: pivot bazli destek/
    direnc seviyesine yaklasmak (proximity_pct) YA DA fiyatin Bollinger
    Bandi'nin alt/ust cizgisine degmesi/disina cikmasi (df'de BB_lower/
    BB_upper kolonlari varsa - bkz. indicators.add_indicators). Ikisi de
    ayni islevi gorur, ikisi de olusursa sebep metninde ikisi de belirtilir.

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

    near_support_pivot = any(
        s > 0 and abs(price - s) / s * 100 < proximity_pct for s in sr_levels.get("support", [])
    )
    near_resistance_pivot = any(
        r > 0 and abs(price - r) / r * 100 < proximity_pct for r in sr_levels.get("resistance", [])
    )

    bb_lower = latest.get("BB_lower")
    bb_upper = latest.get("BB_upper")
    near_support_bb = bb_lower is not None and not pd.isna(bb_lower) and price <= bb_lower
    near_resistance_bb = bb_upper is not None and not pd.isna(bb_upper) and price >= bb_upper

    near_support = near_support_pivot or near_support_bb
    near_resistance = near_resistance_pivot or near_resistance_bb

    if rsi < rsi_oversold and near_support:
        detail = _zone_reason(near_support_pivot, near_support_bb, "destek seviyesine yakin", "Bollinger alt bandina degdi")
        return Signal(symbol, "BUY", f"RSI {rsi:.1f} (asiri satim) + {detail}", price, news)
    if rsi > rsi_overbought and near_resistance:
        detail = _zone_reason(near_resistance_pivot, near_resistance_bb, "direnc seviyesine yakin", "Bollinger ust bandina degdi")
        return Signal(symbol, "SELL", f"RSI {rsi:.1f} (asiri alim) + {detail}", price, news)
    if near_support:
        detail = _zone_reason(near_support_pivot, near_support_bb, "destek seviyesine yakin", "Bollinger alt bandina degdi")
        return Signal(symbol, "WATCH", f"Fiyat {detail} (RSI {rsi:.1f})", price, news)
    if near_resistance:
        detail = _zone_reason(near_resistance_pivot, near_resistance_bb, "direnc seviyesine yakin", "Bollinger ust bandina degdi")
        return Signal(symbol, "WATCH", f"Fiyat {detail} (RSI {rsi:.1f})", price, news)
    return None
