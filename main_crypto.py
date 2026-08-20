import logging
import time

import bybit_trader
import config
from crypto_data_fetcher import get_price_history
from indicators import add_indicators
from notifier import send_telegram_message
from signal_engine import evaluate
from support_resistance import find_support_resistance

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _handle_signal(signal):
    msg = f"[{signal.action}] {signal.symbol} @ {signal.price:.2f}\n{signal.reason}"
    logger.info(msg)
    send_telegram_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, msg)

    if signal.action == "BUY":
        result = bybit_trader.open_position(signal.symbol, "Buy", signal.price)
    elif signal.action == "SELL":
        if config.CRYPTO_ALLOW_SHORT:
            result = bybit_trader.open_position(signal.symbol, "Sell", signal.price)
        else:
            result = bybit_trader.close_position(signal.symbol)
    else:
        return  # WATCH - sadece bildirim, islem yapilmaz

    logger.info("%s icin islem sonucu: %s", signal.symbol, result)


def run_cycle():
    for symbol in config.CRYPTO_SYMBOLS:
        try:
            df = get_price_history(symbol)
            df = add_indicators(df)
            sr = find_support_resistance(df, window=5)

            signal = evaluate(
                symbol,
                df,
                sr,
                proximity_pct=config.CRYPTO_SR_PROXIMITY_PCT,
                rsi_oversold=config.CRYPTO_RSI_OVERSOLD,
                rsi_overbought=config.CRYPTO_RSI_OVERBOUGHT,
            )
            if signal:
                _handle_signal(signal)
            else:
                latest = df.iloc[-1]
                logger.info(
                    "%s: fiyat=%.2f RSI=%.1f destek=%s direnc=%s -> sinyal yok",
                    symbol, latest["Close"], latest["RSI"], sr["support"], sr["resistance"],
                )
        except Exception:
            logger.exception("%s icin dongu basarisiz oldu, sonraki sembole geciliyor", symbol)


def main():
    mode = "TESTNET (sahte bakiye)" if config.BYBIT_TESTNET else "MAINNET (GERCEK PARA)"
    trade_mode = "otomatik emir ACIK" if config.CRYPTO_AUTO_TRADE_ENABLED else "sadece bildirim (dry-run)"
    logger.info(
        "Kripto sinyal botu baslatildi. Ortam: %s | Mod: %s | Semboller: %s",
        mode, trade_mode, config.CRYPTO_SYMBOLS,
    )
    while True:
        run_cycle()
        time.sleep(config.CRYPTO_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot durduruldu.")
