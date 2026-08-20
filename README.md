# US Hisse Senedi Takip & Sinyal Botu

Belirlenen ABD hisselerini (varsayilan: AAPL, MSFT, NVDA, TSLA) takip edip
teknik indikatorlere (RSI, MACD, SMA50/200) ve destek/direnc seviyelerine
gore Telegram uzerinden bildirim gonderen bir sinyal botu.

**Bu proje yatirim tavsiyesi degildir.** Kurallar ornek amaclidir, kendi
risk toleransina gore degistirmelisin. Otomatik emir (gercek/paper trading)
henuz eklenmedi.

## Mimari

```
config.py             # Semboller, esik degerleri, .env'den API key'ler
data_fetcher.py        # yfinance ile OHLCV fiyat verisi
indicators.py           # RSI / MACD / SMA (manuel, pandas_ta kullanmadan)
support_resistance.py  # Pivot bazli destek/direnc tespiti
news_monitor.py         # Finnhub haber cekme + basit anahtar kelime filtresi
signal_engine.py        # Indikator + S/R kurallarina gore BUY/SELL/WATCH sinyali
notifier.py              # Telegram bildirim gonderme
main.py                 # Ana dongu (varsayilan: 5 dakikada bir)
tests/                   # pytest birim testleri (mocklanmis veri ile)
```

`trader.py` (Alpaca ile otomatik emir) bilinclerek eklenmedi — spesifikasyon
geregi bu adim en sona birakildi ve acikca istenmeden yazilmayacak.

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # sonra .env dosyasini doldur
```

`.env` icinde doldurulacaklar:

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — bildirimler icin ([BotFather](https://core.telegram.org/bots#botfather) ile bot olustur, chat id'yi `https://api.telegram.org/bot<token>/getUpdates` ile ogren)
- `NEWS_API_KEY` — [Finnhub](https://finnhub.io/register) ucretsiz API anahtari
- `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` — su an kullanilmiyor, ileri asama icin ayrildi

`config.py` icinde `SYMBOLS`, `RSI_OVERSOLD`/`RSI_OVERBOUGHT`,
`SR_PROXIMITY_PCT` ve `POLL_INTERVAL_SECONDS` degerlerini kendine gore
ayarlayabilirsin.

## Calistirma

```bash
python main.py
```

Telegram bilgileri girilmemisse bot yine calisir, sinyalleri sadece log'a
yazar (bildirim gonderilmez).

## Testler

```bash
pytest -q
```

Tum testler yfinance/Finnhub/Telegram gibi dis servisleri **mockluyor** —
gercek API cagrisi yapmiyor, bu yuzden internet baglantisi olmadan da
calisirlar. Bu proje bu haliyle Claude Code'un genel internete kapali bir
gelistirme ortaminda yazildi; yani canli API baglantisi (gercek fiyat verisi,
gercek Telegram mesaji) hic dogrulanamadi. Kendi makinende calistirmadan once
mutlaka asagidaki gibi tek seferlik bir kontrol yap:

```bash
python -c "from data_fetcher import get_price_history; print(get_price_history('AAPL').tail())"
```

## Yol haritasi

1. ✅ `data_fetcher`, `indicators`, `support_resistance` — fiyat verisi ve teknik analiz
2. ✅ `news_monitor`, `signal_engine` — haber + kural motoru
3. ✅ `notifier`, `main.py` — Telegram bildirimleri ve ana dongu
4. ⏳ `trader.py` (Alpaca paper trading) — sadece acikca istenirse, haftalarca
   sadece-bildirim modunda gozlemledikten sonra eklenmeli

## Onemli notlar

- **Otomatik emir (gercek para) en son adim olmali.** Once haftalarca sadece
  bildirim modunda calistir, sinyallerin mantikli olup olmadigini gozlemle.
- **Paper trading ile basla.** Alpaca'nin paper trading ortami gercek piyasa
  verisiyle calisir ama sanal parayla.
- **API rate limit'lerine dikkat et.** yfinance ve ucretsiz tier'lar sik
  istekte kisitlanabilir.
- Gercek parayla otomatik trading, ulkene ve kullandigin brokera gore
  duzenleyici/vergisel yukumlulukler dogurabilir — mali musavirine danisman
  faydali olur.
