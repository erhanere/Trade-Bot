# US Hisse Senedi + Kripto Takip & Sinyal Botu

İki bağımsız bot barındırır:

1. **Hisse senedi botu** (`main.py`) — ABD hisselerini (varsayılan: AAPL, MSFT,
   NVDA, TSLA) takip edip teknik indikatörlere (RSI, MACD, SMA50/200) ve
   destek/direnç seviyelerine göre Telegram üzerinden bildirim gönderir.
   Sadece bildirim yapar, emir göndermez.
2. **Kripto futures botu** (`main_crypto.py`) — birden fazla kripto sembolünü
   (varsayılan: BTCUSDT, ETHUSDT, MINAUSDT, AVAXUSDT, ENAUSDT, ARBUSDT,
   `.env`'deki `CRYPTO_SYMBOLS` ile değiştirilebilir) eşzamanlı olarak
   **15 dakikalık grafikte** RSI + pivot destek/direnç + Bollinger Bantları
   mantığıyla takip edip Telegram bildirimi gönderir **ve** Bybit üzerinde
   her sembol için bağımsız olarak otomatik long/short pozisyon açıp
   kapatabilir (futures/perpetual, kaldıraçlı).

**Bu proje yatırım tavsiyesi değildir.** Kurallar örnek amaçlıdır, kendi risk
toleransına göre değiştirmelisin. Kripto botu **gerçek para kaybına yol
açabilir** — aşağıdaki güvenlik bölümünü okumadan çalıştırma.

## Mimari

```
config.py                # Semboller, esik degerleri, .env'den API key'ler (hisse + kripto)
data_fetcher.py           # yfinance ile hisse OHLCV fiyat verisi
crypto_data_fetcher.py    # Bybit public kline API'siyle BTC/ETH OHLCV verisi (API key gerekmez)
indicators.py              # RSI / MACD / SMA / Bollinger Bantlari (manuel, pandas_ta kullanmadan) - ortak
support_resistance.py     # Pivot bazli destek/direnc tespiti - hisse+kripto ortak
news_monitor.py            # Finnhub haber cekme + basit anahtar kelime filtresi (sadece hisse)
signal_engine.py           # RSI + pivot S/D + Bollinger Bant kurallarina gore BUY/SELL/WATCH - ortak
notifier.py                 # Telegram bildirim gonderme - ortak
bybit_trader.py            # Bybit futures: bakiye, kaldirac, pozisyon acma/kapama, guvenlik kapilari
main.py                    # Hisse ana dongu (varsayilan: 5 dakikada bir, sadece bildirim)
main_crypto.py              # Kripto ana dongu (varsayilan: 5 dakikada bir, bildirim + opsiyonel emir)
tests/                      # pytest birim testleri (mocklanmis veri ile)
```

`trader.py` (Alpaca ile hisse senedi otomatik emri) bilinçli olarak
eklenmedi — sadece açıkça istenirse yazılacak.

## Sinyal mantığı (kripto botu)

`main_crypto.py`, `CRYPTO_KLINE_INTERVAL` (varsayılan **15 dakika**) ile
çekilen mumlar üzerinde şu üç sinyal kaynağını birleştirir:

1. **RSI (14)** — aşırı satım/alım (`CRYPTO_RSI_OVERSOLD`/`CRYPTO_RSI_OVERBOUGHT`, varsayılan 30/70)
2. **Pivot destek/direnç** — fiyat, `CRYPTO_SR_PROXIMITY_PCT` (varsayılan %3) içine girerse "yakın" sayılır
3. **Bollinger Bantları (20, 2 std)** — fiyat, alt/üst banda `CRYPTO_SR_PROXIMITY_PCT` kadar yaklaşırsa (tam değmesi şart değil) destek/direnç sinyali sayılır

**Destek/direnç bölgesi** = pivot seviyesine yakınlık **VEYA** Bollinger bandına yakınlık — ikisinden biri yeterli, ikisi de olursa Telegram mesajında ikisi de belirtilir (örn. "RSI 19.0 (aşırı satım) + destek seviyesine yakın + Bollinger alt bandına yakın").

**RSI şartı** (`CRYPTO_REQUIRE_RSI_EXTREME`, varsayılan `true`): varsayılan olarak BUY/SELL için RSI'nin de eşiği geçmiş olması gerekir; sadece bölgeye yakınlık varsa (RSI nötrken) WATCH (sadece bildirim, işlem yok) üretilir. `.env`'de `CRYPTO_REQUIRE_RSI_EXTREME=false` yaparsan RSI'ye bakılmaksızın sadece bölgeye yakınlık BUY/SELL açmaya yeter — daha sık işlem, daha fazla risk.

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

## Kurulumu test etme

Bu proje Claude Code'un genel internete kapali bir gelistirme ortaminda
yazildi, yani yfinance/Bybit/Telegram gibi dis servislere hic canli baglanti
kurulamadi — sadece mocklanmis testlerle dogrulandi (`pytest -q`, 52+ test
geciyor). **Botu ilk kez calistirmadan once kendi makinende asagidaki
kontrolu yap**, bu tek komut fiyat verisi cekmeyi, Bybit bakiyeni (API key
girdiysen) ve Telegram bildirimini (token girdiysen) sirayla dener ve
her birinin OK/HATA oldugunu raporlar:

```bash
python check_setup.py
```

Hepsi OK donene kadar `python main_crypto.py` ile tam donguyu baslatma.
`.env`'de sadece `BYBIT_API_KEY`/`SECRET` girip `CRYPTO_AUTO_TRADE_ENABLED=false`
yaparsan, botu once sadece Telegram bildirimi gonderen (emir gondermeyen)
modda birkac gun izleyebilirsin — mantikli sinyaller uretip uretmedigini
gormeden testnet'te bile otomatik emri acmani onermem.

**Testnet kisitlamasi**: Bybit testnet, mainnet'teki her sembolu desteklemez
— enstruman listede gorunse bile (`get_instruments_info` basarili doner)
bazi semboller icin simule edilmis mum/islem verisi olmayabilir
(`get_kline` bos doner). Bot bunu yakalayip o sembolu atlar, calismaya devam
eder. Hangi sembollerin testnette veri dondurdugunu su komutla kontrol
edebilirsin:

```bash
python -c "
from pybit.unified_trading import HTTP
import config
client = HTTP(testnet=config.BYBIT_TESTNET)
for s in config.CRYPTO_SYMBOLS:
    resp = client.get_kline(category='linear', symbol=s, interval='60', limit=5)
    print(s, '-> veri var' if resp['result']['list'] else '-> veri yok (testnette atlanacak)')
"
```
Veri donmeyen sembolleri `.env`'deki `CRYPTO_SYMBOLS` listesinden cikar -
mainnet'e gectiginde (gercek piyasa hareketliligi oldugu icin) muhtemelen
sorunsuz calisirlar.

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
  `CRYPTO_STOP_LOSS_PCT` / `CRYPTO_TAKE_PROFIT_PCT` (varsayilan %10 / %20)
  otomatik eklenir. **Bunlar coin fiyat yuzdesi degil, pozisyon yuzdesidir**
  (kaldiraca gore ROI, Bybit'in "Unrealized P&L(ROI)" sutunuyla ayni anlamda) -
  `bybit_trader.py` fiyat tetikleyicisini `pozisyon_yuzdesi / CRYPTO_LEVERAGE`
  formuluyle hesaplar. Orn. 20x kaldirac + `CRYPTO_STOP_LOSS_PCT=25` ->
  pozisyon %25 zararda kapanir, yani fiyatin sadece %1.25 hareket etmesi
  yeterli. Bu ikisi ve `CRYPTO_LEVERAGE` / `CRYPTO_POSITION_SIZE_PCT`
  `.env`'den degistirilebilir (bkz. `.env.example`) - kod icindeki
  varsayilanlar muhafazakar kalir, riskini sen `.env`'inde ayarlarsin.
- **Short pozisyon kapali** (`CRYPTO_ALLOW_SHORT=False`): SELL sinyali
  sadece mevcut long pozisyonu kapatir, yeni short acmaz. Short'un
  likidasyon riskini anlamadan `True` yapma.
- **Kademeli pozisyon (scale-in), tavansiz**: her sinyalde tek seferde tam
  boyut degil, `CRYPTO_POSITION_SIZE_PCT / CRYPTO_SCALE_IN_TRANCHES` kadar
  kucuk bir kademe acilir (varsayilan 3 kademe). Fiyat destek/direnc
  bolgesine yaklasirken (`CRYPTO_SR_PROXIMITY_PCT`, varsayilan %3) gelen
  her yeni sinyalde bir kademe daha eklenir - **toplam buyuklukte bir tavan
  yok**, firsat oldukca 2., 3., 4. kademe eklenmeye devam eder. Tek fren
  gercek bakiye/marj yetersizligidir (Bybit emri reddeder). Zit yonde acik
  pozisyon varsa atlanir (otomatik yon degistirmez).

## Testler

```bash
pytest -q
```

Tum testler yfinance/Bybit/Finnhub/Telegram gibi dis servisleri **mockluyor**
— gercek API cagrisi yapmiyor. Canli baglanti dogrulamasi icin yukaridaki
"Kurulumu test etme" bolumundeki `check_setup.py`'yi kullan.

## Yol haritasi

1. ✅ `data_fetcher`, `indicators`, `support_resistance` — hisse fiyat verisi ve teknik analiz
2. ✅ `news_monitor`, `signal_engine` — haber + kural motoru
3. ✅ `notifier`, `main.py` — Telegram bildirimleri ve hisse ana dongusu
4. ✅ `crypto_data_fetcher`, `bybit_trader`, `main_crypto.py` — BTC/ETH icin
   Bybit futures botu (testnet varsayilan, guvenlik kapilariyla)
5. ⏳ `trader.py` (Alpaca ile hisse senedi otomatik emri) — sadece acikca
   istenirse eklenmeli
6. ✅ Kripto short pozisyon (`.env`'de `CRYPTO_ALLOW_SHORT=true`) — varsayilan
   kapali, riskini anladiktan sonra acabilirsin

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
