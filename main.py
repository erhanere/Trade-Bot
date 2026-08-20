import logging
import time

import config
from data_fetcher import get_price_history
from indicators import add_indicators
from news_monitor import get_recent_news
from notifier import send_telegram_message
from signal_engine import evaluate
from support_resistance import find_support_resistance

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_cycle():
    for symbol in config.SYMBOLS:
        try:
            df = get_price_history(symbol)
            df = add_indicators(df)
            sr = find_support_resistance(df, window=5)

            news = []
            if config.NEWS_API_KEY:
                try:
                    news = get_recent_news(symbol, config.NEWS_API_KEY, days=config.NEWS_LOOKBACK_DAYS)
                except Exception:
                    logger.exception("%s icin haber cekilemedi", symbol)

            signal = evaluate(symbol, df, sr, news=news)
            if signal:
                msg = f"[{signal.action}] {signal.symbol} @ {signal.price:.2f}\n{signal.reason}"
                logger.info(msg)
                send_telegram_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, msg)
        except Exception:
            logger.exception("%s icin dongu basarisiz oldu, sonraki sembole geciliyor", symbol)


def main():
    logger.info("Sinyal botu baslatildi. Takip edilen semboller: %s", config.SYMBOLS)
    while True:
        run_cycle()
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot durduruldu.")
