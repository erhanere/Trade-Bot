import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return float(value)


def _env_list(name: str, default: list) -> list:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


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

CRYPTO_SYMBOLS = _env_list(
    "CRYPTO_SYMBOLS",
    default=["BTCUSDT", "ETHUSDT", "MINAUSDT", "AVAXUSDT", "ENAUSDT", "ARBUSDT"],
)
CRYPTO_CATEGORY = "linear"  # USDT perpetual futures
CRYPTO_KLINE_INTERVAL = "60"  # dakika (60 = 1 saatlik mumlar)
CRYPTO_KLINE_LIMIT = 300

# RSI/destek-direnc esikleri hisselerden ayri tutuldu; kripto daha volatil,
# ihtiyaca gore ayarla
CRYPTO_RSI_OVERSOLD = 30
CRYPTO_RSI_OVERBOUGHT = 70

# Fiyat, destek/dirence bu yuzdenin icine girince sinyal sayilir. Genis
# tutmak (orn. %3-4) tam seviyeye degmeden, yaklasirken erken pozisyona
# baslamayi saglar - bkz. CRYPTO_SCALE_IN_TRANCHES.
CRYPTO_SR_PROXIMITY_PCT = _env_float("CRYPTO_SR_PROXIMITY_PCT", default=3.0)

# Bybit API kimlik bilgileri
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

# GUVENLIK: varsayilan olarak HER ZAMAN testnet (sahte bakiye). Mainnet'e
# gecmek icin BYBIT_TESTNET=false VE CONFIRM_LIVE_TRADING=true ikisi birden
# .env'de acikca ayarlanmali - bybit_trader.py bu ikisini de kontrol eder.
BYBIT_TESTNET = _env_bool("BYBIT_TESTNET", default=True)
CONFIRM_LIVE_TRADING = _env_bool("CONFIRM_LIVE_TRADING", default=False)

# Kaldirac (futures/perpetual icin). Yuksek kaldirac = likidasyona daha az
# mesafe; stop-loss'un likidasyon mesafesinin icinde kaldigindan emin ol.
CRYPTO_LEVERAGE = _env_float("CRYPTO_LEVERAGE", default=3)

# Pozisyon buyuklugu: bakiyenin yuzdesi olarak (orn. 5.0 => bakiyenin %5'i).
# Tek bir "tam" pozisyonun buyuklugu budur - gercekte her kademe bunun
# CRYPTO_SCALE_IN_TRANCHES'e bolunmus kadaridir (bkz. asagisi).
CRYPTO_POSITION_SIZE_PCT = _env_float("CRYPTO_POSITION_SIZE_PCT", default=5.0)

# Her kademe (tranche) CRYPTO_POSITION_SIZE_PCT / CRYPTO_SCALE_IN_TRANCHES
# kadar kucuk acilir. TOPLAM BUYUKLUKTE BIR TAVAN YOK: destek/direnc
# bolgesine yaklasirken/kaldigi surece her yeni sinyalde 2., 3., 4. kademe
# eklenmeye devam eder - fırsat oldukca bot pozisyon biriktirir. Tek fren
# gercek bakiye/marj yetersizligidir (Bybit emri reddeder).
CRYPTO_SCALE_IN_TRANCHES = max(1, int(_env_float("CRYPTO_SCALE_IN_TRANCHES", default=3)))

# Risk yonetimi: her pozisyona otomatik eklenen stop-loss / take-profit.
# DIKKAT: bunlar COIN FIYAT YUZDESI DEGIL, POZISYON YUZDESIDIR (kaldiraca
# gore ROI - Bybit'in "Unrealized P&L(ROI)" sutunuyla ayni anlamda). Orn.
# CRYPTO_LEVERAGE=20 ve CRYPTO_STOP_LOSS_PCT=25 ise pozisyon %25 zarara
# ulastiginda kapanir - bu da fiyatin sadece %25/20=%1.25 hareket etmesi
# demektir (bybit_trader.py bu donusumu otomatik yapar). Varsayilanlar
# muhafazakar (1:2 risk/odul); kendi degerlerini .env'de ayarla.
CRYPTO_STOP_LOSS_PCT = _env_float("CRYPTO_STOP_LOSS_PCT", default=10.0)
CRYPTO_TAKE_PROFIT_PCT = _env_float("CRYPTO_TAKE_PROFIT_PCT", default=20.0)

# Short pozisyon acma - varsayilan kapali, SELL sinyali sadece mevcut long
# pozisyonu kapatir. .env'de CRYPTO_ALLOW_SHORT=true yapmadan once short'un
# likidasyon riskini anla (fiyat yukselirse short pozisyon zarar eder).
CRYPTO_ALLOW_SHORT = _env_bool("CRYPTO_ALLOW_SHORT", default=False)

# Otomatik emir - testnet'te varsayilan acik (sahte bakiye, risk yok).
# Mainnet'te CONFIRM_LIVE_TRADING olmadan otomatik emir asla calismaz.
CRYPTO_AUTO_TRADE_ENABLED = _env_bool("CRYPTO_AUTO_TRADE_ENABLED", default=True)

CRYPTO_POLL_INTERVAL_SECONDS = 300
