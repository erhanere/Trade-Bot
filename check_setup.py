"""Kripto botunu tam dongude calistirmadan once kurulumu dogrulayan hizli kontrol.

Kullanim:
    python check_setup.py
"""

import sys

import config


def check(label: str, fn):
    print(f"-> {label} ...", end=" ", flush=True)
    try:
        result = fn()
        print(f"OK ({result})")
        return True
    except Exception as exc:
        print(f"HATA: {exc}")
        return False


def main():
    print("=== Trade-Bot kurulum kontrolu ===\n")
    ok = True

    print(f"Bybit ortami: {'TESTNET (sahte bakiye)' if config.BYBIT_TESTNET else 'MAINNET (GERCEK PARA!)'}")
    print(f"Otomatik emir: {'ACIK' if config.CRYPTO_AUTO_TRADE_ENABLED else 'KAPALI (dry-run)'}\n")

    from crypto_data_fetcher import get_price_history

    for symbol in config.CRYPTO_SYMBOLS:
        ok &= check(
            f"{symbol} fiyat verisi (Bybit public API)",
            lambda s=symbol: f"son kapanis {get_price_history(s, limit=5)['Close'].iloc[-1]:.2f}",
        )

    if config.BYBIT_API_KEY and config.BYBIT_API_SECRET:
        import bybit_trader

        ok &= check("Bybit hesap bakiyesi (API key gerekli)", lambda: f"{bybit_trader.get_usdt_balance():.2f} USDT")
        for symbol in config.CRYPTO_SYMBOLS:
            ok &= check(f"{symbol} enstruman bilgisi", lambda s=symbol: bybit_trader.get_instrument_info(s)["symbol"])
    else:
        print("-> Bybit API key/secret girilmemis, bakiye/enstruman kontrolu atlaniyor")
        print("   (sadece veri cekme + bildirim modunu test edebilirsin)")

    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        from notifier import send_telegram_message

        ok &= check(
            "Telegram test mesaji",
            lambda: "gonderildi"
            if send_telegram_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, "Trade-Bot kurulum kontrolu basarili.")
            else (_ for _ in ()).throw(RuntimeError("gonderilemedi")),
        )
    else:
        print("-> Telegram token/chat_id girilmemis, bildirim testi atlaniyor")

    print("\n=== Sonuc:", "HEPSI BASARILI" if ok else "BAZI KONTROLLER BASARISIZ", "===")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
