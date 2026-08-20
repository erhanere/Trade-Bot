import config
import main_crypto
from signal_engine import Signal


def test_buy_signal_opens_long(monkeypatch):
    monkeypatch.setattr(main_crypto, "send_telegram_message", lambda *a, **k: True)
    calls = []
    monkeypatch.setattr(main_crypto.bybit_trader, "open_position", lambda symbol, side, price: calls.append(("open", symbol, side, price)))
    monkeypatch.setattr(main_crypto.bybit_trader, "close_position", lambda symbol: calls.append(("close", symbol)))

    signal = Signal("BTCUSDT", "BUY", "RSI dusuk + destek", 50000.0)
    main_crypto._handle_signal(signal)

    assert calls == [("open", "BTCUSDT", "Buy", 50000.0)]


def test_sell_signal_closes_position_when_shorting_disabled(monkeypatch):
    monkeypatch.setattr(config, "CRYPTO_ALLOW_SHORT", False)
    monkeypatch.setattr(main_crypto, "send_telegram_message", lambda *a, **k: True)
    calls = []
    monkeypatch.setattr(main_crypto.bybit_trader, "open_position", lambda symbol, side, price: calls.append(("open", symbol, side, price)))
    monkeypatch.setattr(main_crypto.bybit_trader, "close_position", lambda symbol: calls.append(("close", symbol)))

    signal = Signal("ETHUSDT", "SELL", "RSI yuksek + direnc", 3000.0)
    main_crypto._handle_signal(signal)

    assert calls == [("close", "ETHUSDT")]


def test_sell_signal_opens_short_when_shorting_enabled(monkeypatch):
    monkeypatch.setattr(config, "CRYPTO_ALLOW_SHORT", True)
    monkeypatch.setattr(main_crypto, "send_telegram_message", lambda *a, **k: True)
    calls = []
    monkeypatch.setattr(main_crypto.bybit_trader, "open_position", lambda symbol, side, price: calls.append(("open", symbol, side, price)))
    monkeypatch.setattr(main_crypto.bybit_trader, "close_position", lambda symbol: calls.append(("close", symbol)))

    signal = Signal("ETHUSDT", "SELL", "RSI yuksek + direnc", 3000.0)
    main_crypto._handle_signal(signal)

    assert calls == [("open", "ETHUSDT", "Sell", 3000.0)]


def test_watch_signal_only_notifies_no_trade(monkeypatch):
    sent = []
    monkeypatch.setattr(main_crypto, "send_telegram_message", lambda token, chat_id, text: sent.append(text))
    calls = []
    monkeypatch.setattr(main_crypto.bybit_trader, "open_position", lambda symbol, side, price: calls.append(("open", symbol, side, price)))
    monkeypatch.setattr(main_crypto.bybit_trader, "close_position", lambda symbol: calls.append(("close", symbol)))

    signal = Signal("BTCUSDT", "WATCH", "Direnc seviyesine yakin", 51000.0)
    main_crypto._handle_signal(signal)

    assert calls == []
    assert len(sent) == 1
