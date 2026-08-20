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
    require_rsi_extreme: bool = True,
) -> "Signal | None":
    """Indikator + destek/direnc + Bollinger Bant kurallarina gore bir sinyal uretir.

    "Destek/direnc bolgesi" iki kaynaktan gelebilir, ikisi de AYNI
    proximity_pct yakinlik esigini kullanir (fiyatin tam seviyeye degmesi
    sart degil, yaklasmasi yeterli - kademeli pozisyon acmayi destekler):
    - pivot bazli destek/direnc seviyesine yaklasmak
    - Bollinger Bandi'nin alt/ust cizgisine yaklasmak (df'de BB_lower/
      BB_upper kolonlari varsa - bkz. indicators.add_indicators)
    Ikisi de olusursa sebep metninde ikisi de belirtilir.

    require_rsi_extreme=True (varsayilan) iken BUY/SELL icin RSI'nin de
    asiri satim/alim esigini gecmis olmasi sart - sadece bolgeye yakinlik
    varsa (RSI notrken) WATCH (bildirim, islem yok) uretilir. False
    yapilirsa RSI'ye bakilmaksizin sadece bolgeye yakinlik BUY/SELL
    uretmeye yeter (WATCH fiilen devre disi kalir) - daha sik/riskli.

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
    near_support_bb = (
        bb_lower is not None and not pd.isna(bb_lower) and bb_lower > 0
        and abs(price - bb_lower) / bb_lower * 100 < proximity_pct
    )
    near_resistance_bb = (
        bb_upper is not None and not pd.isna(bb_upper) and bb_upper > 0
        and abs(price - bb_upper) / bb_upper * 100 < proximity_pct
    )

    near_support = near_support_pivot or near_support_bb
    near_resistance = near_resistance_pivot or near_resistance_bb

    rsi_oversold_hit = rsi < rsi_oversold
    rsi_overbought_hit = rsi > rsi_overbought
    buy_gate = rsi_oversold_hit or not require_rsi_extreme
    sell_gate = rsi_overbought_hit or not require_rsi_extreme

    if buy_gate and near_support:
        detail = _zone_reason(near_support_pivot, near_support_bb, "destek seviyesine yakin", "Bollinger alt bandina yakin")
        rsi_label = "asiri satim" if rsi_oversold_hit else "notr"
        return Signal(symbol, "BUY", f"RSI {rsi:.1f} ({rsi_label}) + {detail}", price, news)
    if sell_gate and near_resistance:
        detail = _zone_reason(near_resistance_pivot, near_resistance_bb, "direnc seviyesine yakin", "Bollinger ust bandina yakin")
        rsi_label = "asiri alim" if rsi_overbought_hit else "notr"
        return Signal(symbol, "SELL", f"RSI {rsi:.1f} ({rsi_label}) + {detail}", price, news)
    if near_support:
        detail = _zone_reason(near_support_pivot, near_support_bb, "destek seviyesine yakin", "Bollinger alt bandina yakin")
        return Signal(symbol, "WATCH", f"Fiyat {detail} (RSI {rsi:.1f})", price, news)
    if near_resistance:
        detail = _zone_reason(near_resistance_pivot, near_resistance_bb, "direnc seviyesine yakin", "Bollinger ust bandina yakin")
        return Signal(symbol, "WATCH", f"Fiyat {detail} (RSI {rsi:.1f})", price, news)
    return None
