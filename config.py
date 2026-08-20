import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")

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

# ---------------------------------------------------------------------------
# Kripto (Bybit) ayarlari
# ---------------------------------------------------------------------------

CRYPTO_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
CRYPTO_CATEGORY = "linear"  # USDT perpetual futures
CRYPTO_KLINE_INTERVAL = "60"  # dakika (60 = 1 saatlik mumlar)
CRYPTO_KLINE_LIMIT = 300

# RSI/destek-direnc esikleri hisselerden ayri tutuldu; kripto daha volatil,
# ihtiyaca gore ayarla
CRYPTO_RSI_OVERSOLD = 30
CRYPTO_RSI_OVERBOUGHT = 70
CRYPTO_SR_PROXIMITY_PCT = 1.5

# Bybit API kimlik bilgileri
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

# GUVENLIK: varsayilan olarak HER ZAMAN testnet (sahte bakiye). Mainnet'e
# gecmek icin BYBIT_TESTNET=false VE CONFIRM_LIVE_TRADING=true ikisi birden
# .env'de acikca ayarlanmali - bybit_trader.py bu ikisini de kontrol eder.
BYBIT_TESTNET = _env_bool("BYBIT_TESTNET", default=True)
CONFIRM_LIVE_TRADING = _env_bool("CONFIRM_LIVE_TRADING", default=False)

# Kaldirac (futures/perpetual icin)
CRYPTO_LEVERAGE = 3

# Pozisyon buyuklugu: bakiyenin yuzdesi olarak (orn. 5.0 => bakiyenin %5'i)
CRYPTO_POSITION_SIZE_PCT = 5.0

# Risk yonetimi: her pozisyona otomatik eklenen stop-loss / take-profit (%)
CRYPTO_STOP_LOSS_PCT = 3.0
CRYPTO_TAKE_PROFIT_PCT = 6.0

# Short pozisyon acma - v1'de kapali, SELL sinyali sadece mevcut long
# pozisyonu kapatir. True yapmadan once short'un likidasyon riskini anla.
CRYPTO_ALLOW_SHORT = False

# Otomatik emir - testnet'te varsayilan acik (sahte bakiye, risk yok).
# Mainnet'te CONFIRM_LIVE_TRADING olmadan otomatik emir asla calismaz.
CRYPTO_AUTO_TRADE_ENABLED = _env_bool("CRYPTO_AUTO_TRADE_ENABLED", default=True)

CRYPTO_POLL_INTERVAL_SECONDS = 300
