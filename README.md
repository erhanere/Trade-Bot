# US Hisse Senedi + Kripto Takip & Sinyal Botu

İki bağımsız bot barındırır:

1. **Hisse senedi botu** (`main.py`) — ABD hisselerini (varsayılan: AAPL, MSFT,
   NVDA, TSLA) takip edip teknik indikatörlere (RSI, MACD, SMA50/200) ve
   destek/direnç seviyelerine göre Telegram üzerinden bildirim gönderir.
   Sadece bildirim yapar, emir göndermez.
2. **Kripto futures botu** (`main_crypto.py`) — BTC/ETH'i (varsayılan:
   BTCUSDT, ETHUSDT) aynı RSI + destek/direnç mantığıyla takip edip Telegram
   bildirimi gönderir **ve** Bybit üzerinde otomatik long/short pozisyon
   açıp kapatabilir (futures/perpetual, kaldıraçlı).

**Bu proje yatırım tavsiyesi değildir.** Kurallar örnek amaçlıdır, kendi risk
toleransına göre değiştirmelisin. Kripto botu **gerçek para kaybına yol
açabilir** — aşağıdaki güvenlik bölümünü okumadan çalıştırma.

## Mimari

```
config.py                # Semboller, esik degerleri, .env'den API key'ler (hisse + kripto)
data_fetcher.py           # yfinance ile hisse OHLCV fiyat verisi
crypto_data_fetcher.py    # Bybit public kline API'siyle BTC/ETH OHLCV verisi (API key gerekmez)
indicators.py              # RSI / MACD / SMA (manuel, pandas_ta kullanmadan) - hisse+kripto ortak
support_resistance.py     # Pivot bazli destek/direnc tespiti - hisse+kripto ortak
news_monitor.py            # Finnhub haber cekme + basit anahtar kelime filtresi (sadece hisse)
signal_engine.py           # Indikator + S/R kurallarina gore BUY/SELL/WATCH sinyali - ortak
notifier.py                 # Telegram bildirim gonderme - ortak
bybit_trader.py            # Bybit futures: bakiye, kaldirac, pozisyon acma/kapama, guvenlik kapilari
main.py                    # Hisse ana dongu (varsayilan: 5 dakikada bir, sadece bildirim)
main_crypto.py              # Kripto ana dongu (varsayilan: 5 dakikada bir, bildirim + opsiyonel emir)
tests/                      # pytest birim testleri (mocklanmis veri ile)
```

`trader.py` (Alpaca ile hisse senedi otomatik emri) bilinçli olarak
eklenmedi — sadece açıkça istenirse yazılacak.

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # sonra .env dosyasini doldur
```

`.env` icinde doldurulacaklar:

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — bildirimler icin ([BotFather](https://core.telegram.org/bots#botfather) ile bot olustur, chat id'yi `https://api.telegram.org/bot<token>/getUpdates` ile ogren)
- `NEWS_API_KEY` — [Finnhub](https://finnhub.io/register) ucretsiz API anahtari (sadece hisse botu icin)
- `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` — su an kullanilmiyor, ileri asama icin ayrildi
- `BYBIT_API_KEY` / `BYBIT_API_SECRET` — kripto botu icin, asagidaki "Bybit kurulumu" bolumune bak

`config.py` icinde `SYMBOLS`, `RSI_OVERSOLD`/`RSI_OVERBOUGHT`,
`SR_PROXIMITY_PCT` ve `POLL_INTERVAL_SECONDS` degerlerini kendine gore
ayarlayabilirsin. Kripto icin ayni ayarlarin `CRYPTO_` on ekli karsiliklari var.

## Calistirma

```bash
python main.py          # Hisse senedi botu (sadece bildirim)
python main_crypto.py   # Kripto botu (bildirim + testnet'te varsayilan otomatik emir)
```

Telegram bilgileri girilmemisse botlar yine calisir, sinyalleri sadece
log'a yazar (bildirim gonderilmez).

## Bybit kurulumu (kripto botu icin)

1. **Once testnet hesabi ac**: https://testnet.bybit.com — gercek hesabindan
   bagimsiz, sahte bakiye verir. API anahtarini buradan olustur
   (testnet.bybit.com/app/user/api-management), `.env`'e `BYBIT_API_KEY` /
   `BYBIT_API_SECRET` olarak yaz.
2. `.env` dosyasinda varsayilan ayarlar zaten guvenli tarafta:
   ```
   BYBIT_TESTNET=true
   CONFIRM_LIVE_TRADING=false
   CRYPTO_AUTO_TRADE_ENABLED=true
   ```
   Bu haliyle bot **sadece testnet'te** (sahte bakiye) otomatik islem yapar.
3. `python main_crypto.py` calistir, botun testnet hesabinda pozisyon
   acip kapadigini https://testnet.bybit.com uzerinden gozlemle.
4. **Sadece haftalarca testnet'te gozlemledikten ve stratejiyi guvendigin bir
   noktaya getirdikten sonra** mainnet'e (gercek para) gecmeyi dusun.

### Guvenlik katmanlari (kripto botu)

Kod, gercek parayla yanlislikla islem yapmayi zorlastirmak icin birden
fazla kapiya sahip:

- **Varsayilan her zaman testnet** (`BYBIT_TESTNET=true`). Mainnet'e gecmek
  icin bunu bilinçli olarak `false` yapman gerekir.
- **Mainnet'te ekstra onay sarti**: `BYBIT_TESTNET=false` olsa bile,
  `CONFIRM_LIVE_TRADING=true` acikca ayarlanmadan `bybit_trader.py` gercek
  emir gondermeyi reddeder (`RuntimeError` firlatir).
- **CRYPTO_AUTO_TRADE_ENABLED=false** yaparsan bot hicbir gercek emir
  gondermez, sadece "şunu yapacaktım" seklinde loglar (dry-run) ve Telegram
  bildirimi gonderir — stratejini once bu modda gozlemleyebilirsin.
- **Otomatik stop-loss / take-profit**: her acilan pozisyona
  `CRYPTO_STOP_LOSS_PCT` / `CRYPTO_TAKE_PROFIT_PCT` (varsayilan %3 / %6)
  otomatik eklenir.
- **Short pozisyon kapali** (`CRYPTO_ALLOW_SHORT=False`): SELL sinyali
  sadece mevcut long pozisyonu kapatir, yeni short acmaz. Short'un
  likidasyon riskini anlamadan `True` yapma.
- **Pozisyon ustune eklenmez**: bir sembolde zaten acik pozisyon varsa yeni
  BUY sinyali atlanir, ustune pozisyon eklenmez.

## Testler

```bash
pytest -q
```

Tum testler yfinance/Bybit/Finnhub/Telegram gibi dis servisleri **mockluyor**
— gercek API cagrisi yapmiyor, bu yuzden internet baglantisi olmadan da
calisirlar. Bu proje bu haliyle Claude Code'un genel internete kapali bir
gelistirme ortaminda yazildi; yani canli API baglantisi (gercek fiyat verisi,
gercek Telegram mesaji, gercek Bybit testnet emri) hic dogrulanamadi. Kendi
makinende calistirmadan once mutlaka tek seferlik bir kontrol yap:

```bash
python -c "from data_fetcher import get_price_history; print(get_price_history('AAPL').tail())"
python -c "from crypto_data_fetcher import get_price_history; print(get_price_history('BTCUSDT').tail())"
```

## Yol haritasi

1. ✅ `data_fetcher`, `indicators`, `support_resistance` — hisse fiyat verisi ve teknik analiz
2. ✅ `news_monitor`, `signal_engine` — haber + kural motoru
3. ✅ `notifier`, `main.py` — Telegram bildirimleri ve hisse ana dongusu
4. ✅ `crypto_data_fetcher`, `bybit_trader`, `main_crypto.py` — BTC/ETH icin
   Bybit futures botu (testnet varsayilan, guvenlik kapilariyla)
5. ⏳ `trader.py` (Alpaca ile hisse senedi otomatik emri) — sadece acikca
   istenirse eklenmeli
6. ⏳ Kripto short pozisyon (`CRYPTO_ALLOW_SHORT=True`) — su an kapali,
   istersen ayri bir adim olarak gelistirilebilir

## Onemli notlar

- **Otomatik emir (gercek para) en son adim olmali.** Once haftalarca sadece
  testnet/bildirim modunda calistir, sinyallerin mantikli olup olmadigini
  gozlemle.
- **Kripto botu varsayilan olarak testnet'te otomatik emir gonderir**
  (sahte bakiye, sifir risk) — mainnet'e gecis icin yukaridaki "Bybit
  kurulumu" bolumundeki guvenlik katmanlarini oku.
- **API rate limit'lerine dikkat et.** yfinance, Bybit ve ucretsiz tier'lar
  sik istekte kisitlanabilir.
- **Kaldiracli islem likidasyon riski tasir.** `CRYPTO_LEVERAGE` ve
  `CRYPTO_POSITION_SIZE_PCT` degerlerini riskini anlamadan yukseltme.
- Gercek parayla otomatik trading, ulkene ve kullandigin brokera/borsaya gore
  duzenleyici/vergisel yukumlulukler dogurabilir — mali musavirine danisman
  faydali olur.
