import os

from dotenv import load_dotenv

load_dotenv()

# Takip edilen semboller
SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA"]

# RSI esikleri
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Destek/direnc tespiti
SR_LOOKBACK_DAYS = 60
SR_PROXIMITY_PCT = 1.0  # fiyat, destek/dirence %1 yaklasinca sinyal say

# Dongu araligi (saniye)
POLL_INTERVAL_SECONDS = 300

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Alpaca (ileri asama - trader.py henuz yok)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # PAPER TRADING - gercek para degil

# Haber
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_LOOKBACK_DAYS = 7

# Otomatik emir - False'tan True'ya gecmeden once haftalarca paper trading ile test edin
AUTO_TRADE_ENABLED = False
