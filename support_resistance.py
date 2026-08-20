import pandas as pd


def find_support_resistance(df: pd.DataFrame, window: int = 5, num_levels: int = 3) -> dict:
    """Pivot-nokta bazli destek/direnc tespiti.

    Bir gun, kendisinden once ve sonraki `window` gun icinde en yuksek/dusuk
    ise pivot direnc/destek sayilir. Sonuclar, son kapanis fiyatina en yakin
    olacak sekilde filtrelenir: direnc seviyeleri fiyatin ustunde (yakindan
    uzaga), destek seviyeleri fiyatin altinda (yakindan uzaga) siralanir.
    """
    if len(df) < 2 * window + 1:
        return {"resistance": [], "support": []}

    highs = df["High"]
    lows = df["Low"]
    current_price = df["Close"].iloc[-1]

    resistance_levels = []
    support_levels = []
    for i in range(window, len(df) - window):
        window_slice_high = highs.iloc[i - window : i + window + 1]
        window_slice_low = lows.iloc[i - window : i + window + 1]
        if highs.iloc[i] == window_slice_high.max():
            resistance_levels.append(highs.iloc[i])
        if lows.iloc[i] == window_slice_low.min():
            support_levels.append(lows.iloc[i])

    resistance_above = sorted(r for r in set(resistance_levels) if r >= current_price)
    support_below = sorted((s for s in set(support_levels) if s <= current_price), reverse=True)

    return {
        "resistance": resistance_above[:num_levels],
        "support": support_below[:num_levels],
    }
