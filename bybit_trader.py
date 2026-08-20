import logging
import math

from pybit.exceptions import InvalidRequestError
from pybit.unified_trading import HTTP

import config

logger = logging.getLogger(__name__)

# Bybit "leverage not modified" hata kodu - istenen kaldirac zaten ayarli,
# hata degil, sorunsuz devam edilebilir.
_LEVERAGE_NOT_MODIFIED = 110043


def _client() -> HTTP:
    return HTTP(
        testnet=config.BYBIT_TESTNET,
        api_key=config.BYBIT_API_KEY,
        api_secret=config.BYBIT_API_SECRET,
    )


def _assert_safe_to_trade():
    """Mainnet'te gercek emir gondermeden once ekstra bilincli onay ister."""
    if not config.BYBIT_TESTNET and not config.CONFIRM_LIVE_TRADING:
        raise RuntimeError(
            "Mainnet'te otomatik emir gondermek icin .env dosyasinda "
            "CONFIRM_LIVE_TRADING=true ayarlaman gerekiyor. Once haftalarca "
            "testnet'te (BYBIT_TESTNET=true) test etmeni oneririz."
        )


def get_usdt_balance() -> float:
    resp = _client().get_wallet_balance(accountType="UNIFIED", coin="USDT")
    if resp.get("retCode") != 0:
        raise ValueError(f"Bakiye alinamadi: {resp.get('retMsg')}")
    accounts = resp["result"]["list"]
    if not accounts:
        return 0.0
    for coin in accounts[0]["coin"]:
        if coin["coin"] == "USDT":
            return float(coin["walletBalance"])
    return 0.0


def get_instrument_info(symbol: str, category: str = None) -> dict:
    category = category or config.CRYPTO_CATEGORY
    resp = _client().get_instruments_info(category=category, symbol=symbol)
    if resp.get("retCode") != 0:
        raise ValueError(f"{symbol} enstruman bilgisi alinamadi: {resp.get('retMsg')}")
    items = resp["result"]["list"]
    if not items:
        raise ValueError(f"{symbol} icin enstruman bulunamadi")
    return items[0]


def round_qty(qty: float, qty_step: float, min_qty: float) -> float:
    """Miktari borsanin izin verdigi adim buyuklugune yuvarlar (asagi).

    Minimum emir miktarinin altinda kalirsa 0 dondurur (emir gonderilmemeli).
    """
    if qty_step <= 0:
        return qty
    steps = math.floor(qty / qty_step)
    rounded = round(steps * qty_step, 10)
    if rounded < min_qty:
        return 0.0
    return rounded


def round_price(price: float, tick_size: float) -> float:
    """Fiyati borsanin izin verdigi tick buyuklugune (en yakina) yuvarlar.

    Ucuz altcoin'lerde (orn. $0.10) sabit 2 ondalik yuvarlama stop-loss ve
    take-profit'i ayni degere cakistirip Bybit'in emri reddetmesine yol
    acar - her sembolun kendi priceFilter.tickSize'ina gore yuvarlamak gerekir.
    """
    if tick_size <= 0:
        return price
    steps = round(price / tick_size)
    return round(steps * tick_size, 10)


def _decimal_places(step_str: str) -> int:
    """'0.0001' -> 4, '0.01' -> 2, '1' -> 0. Bybit'e string gonderirken
    bilimsel gosterim (1e-05) veya yanlis ondalik sayisi olusmasin diye."""
    if "." not in step_str:
        return 0
    return len(step_str.split(".")[1].rstrip("0"))


def _target_notional(balance: float) -> float:
    """Bakiyenin CRYPTO_POSITION_SIZE_PCT'i ve CRYPTO_LEVERAGE kadar kaldiracla
    ulasilmak istenen TAM hedef pozisyon buyuklugu (notional, USDT)."""
    return balance * (config.CRYPTO_POSITION_SIZE_PCT / 100) * config.CRYPTO_LEVERAGE


def calculate_position_qty(
    symbol: str,
    price: float,
    balance: float,
    notional: float = None,
    qty_step: float = None,
    min_qty: float = None,
) -> float:
    """Verilen notional (USDT) buyuklugune karsilik gelen miktari, borsa
    hassasiyetine (qtyStep/minOrderQty) yuvarlayarak hesaplar.

    notional verilmezse tam hedef pozisyon buyuklugu kullanilir. qty_step/
    min_qty verilmezse enstruman bilgisi ayrica cekilir (bkz. open_position -
    orada zaten cekildigi icin tekrar API cagrisi yapmamak adina gecilir).
    """
    if qty_step is None or min_qty is None:
        info = get_instrument_info(symbol)
        lot = info["lotSizeFilter"]
        qty_step = float(lot["qtyStep"])
        min_qty = float(lot["minOrderQty"])

    if notional is None:
        notional = _target_notional(balance)
    return round_qty(notional / price, qty_step, min_qty)


def set_leverage(symbol: str, leverage: float = None, category: str = None):
    leverage = leverage or config.CRYPTO_LEVERAGE
    category = category or config.CRYPTO_CATEGORY
    # Bybit tam sayi kaldiraclari "3.0" degil "3" seklinde bekliyor
    leverage_str = f"{leverage:g}"
    try:
        resp = _client().set_leverage(
            category=category, symbol=symbol, buyLeverage=leverage_str, sellLeverage=leverage_str
        )
    except InvalidRequestError as exc:
        # pybit "leverage not modified" gibi bazi hata kodlarinda dict degil
        # exception firlatir - istenen kaldirac zaten ayarliysa sorun degil.
        if exc.status_code == _LEVERAGE_NOT_MODIFIED:
            return
        raise ValueError(f"{symbol} kaldirac ayarlanamadi: {exc.message}") from exc

    if resp.get("retCode") not in (0, _LEVERAGE_NOT_MODIFIED):
        raise ValueError(f"{symbol} kaldirac ayarlanamadi: {resp.get('retMsg')}")


def get_open_position(symbol: str, category: str = None):
    category = category or config.CRYPTO_CATEGORY
    resp = _client().get_positions(category=category, symbol=symbol)
    if resp.get("retCode") != 0:
        raise ValueError(f"{symbol} pozisyon bilgisi alinamadi: {resp.get('retMsg')}")
    for pos in resp["result"]["list"]:
        if float(pos.get("size", 0) or 0) > 0:
            return pos
    return None


def open_position(symbol: str, side: str, price: float, category: str = None) -> dict:
    """Yeni pozisyon acar ya da mevcut ayni yonlu pozisyona kademe ekler.
    side: 'Buy' (long) veya 'Sell' (short).

    Her sinyalde CRYPTO_POSITION_SIZE_PCT'in CRYPTO_SCALE_IN_TRANCHES'e
    bolunmus kadar kucuk bir kademe acilir/eklenir - TOPLAM BUYUKLUKTE BIR
    TAVAN YOK: fiyat destek/direnc bolgesinde kaldigi surece (ya da tekrar
    yaklastikca) her yeni sinyalde 2., 3., 4. kademe eklenmeye devam eder.
    Tek fren, gercek para/marj yetersizligi ve Bybit'in kendi limitleridir.

    - Zit yonde acik pozisyon varsa atlar (once elle kapatilmali, otomatik
      yon degistirmez).
    - CRYPTO_AUTO_TRADE_ENABLED=False ise gercek emir gondermez, sadece ne
      yapilacagini loglar (dry-run) - Telegram-only test modunu destekler.
    - Mainnet'te CONFIRM_LIVE_TRADING onayi olmadan calismaz.
    """
    category = category or config.CRYPTO_CATEGORY

    existing = get_open_position(symbol, category=category)
    if existing is not None and existing.get("side") != side:
        logger.info("%s icin ters yonde acik pozisyon var, atlaniyor", symbol)
        return {"skipped": True, "reason": "opposite_position_exists"}

    balance = get_usdt_balance()
    tranche_notional = _target_notional(balance) / config.CRYPTO_SCALE_IN_TRANCHES

    # Enstruman hassasiyetini (miktar adimi + fiyat tick'i) tek seferde cek -
    # ucuz altcoin'lerde (orn. $0.10) sabit ondalik yuvarlama SL/TP'yi ayni
    # degere cakistirip Bybit'in emri reddetmesine yol acabiliyor.
    info = get_instrument_info(symbol, category=category)
    lot = info["lotSizeFilter"]
    qty_step = float(lot["qtyStep"])
    min_qty = float(lot["minOrderQty"])
    qty_decimals = _decimal_places(lot["qtyStep"])

    price_filter = info["priceFilter"]
    tick_size = float(price_filter["tickSize"])
    price_decimals = _decimal_places(price_filter["tickSize"])

    qty = calculate_position_qty(
        symbol, price, balance, notional=tranche_notional, qty_step=qty_step, min_qty=min_qty
    )
    if qty <= 0:
        logger.warning("%s icin hesaplanan miktar minimumun altinda, emir gonderilmiyor", symbol)
        return {"skipped": True, "reason": "qty_too_small"}

    # CRYPTO_STOP_LOSS_PCT / CRYPTO_TAKE_PROFIT_PCT pozisyon yuzdesi (marjine
    # gore ROI) olarak tanimli, coin fiyat yuzdesi degil. Bybit'in SL/TP
    # alanlari her zaman fiyat tetikleyicisi bekledigi icin kaldiraca bolerek
    # gercek fiyat hareketine ceviriyoruz (ROI% = fiyat_hareketi% * kaldirac).
    leverage = config.CRYPTO_LEVERAGE
    stop_loss_price_pct = (config.CRYPTO_STOP_LOSS_PCT / 100) / leverage
    take_profit_price_pct = (config.CRYPTO_TAKE_PROFIT_PCT / 100) / leverage
    if side == "Buy":
        stop_loss = price * (1 - stop_loss_price_pct)
        take_profit = price * (1 + take_profit_price_pct)
    else:
        stop_loss = price * (1 + stop_loss_price_pct)
        take_profit = price * (1 - take_profit_price_pct)

    stop_loss = round_price(stop_loss, tick_size)
    take_profit = round_price(take_profit, tick_size)
    qty_str = f"{qty:.{qty_decimals}f}"
    stop_loss_str = f"{stop_loss:.{price_decimals}f}"
    take_profit_str = f"{take_profit:.{price_decimals}f}"

    if not config.CRYPTO_AUTO_TRADE_ENABLED:
        logger.info(
            "[DRY-RUN] %s %s qty=%s (yeni kademe) @ ~%s SL=%s TP=%s "
            "(CRYPTO_AUTO_TRADE_ENABLED=False, emir gonderilmedi)",
            symbol, side, qty_str, f"{price:.{price_decimals}f}", stop_loss_str, take_profit_str,
        )
        return {"dry_run": True, "symbol": symbol, "side": side, "qty": qty}

    _assert_safe_to_trade()
    set_leverage(symbol, category=category)

    resp = _client().place_order(
        category=category,
        symbol=symbol,
        side=side,
        orderType="Market",
        qty=qty_str,
        stopLoss=stop_loss_str,
        takeProfit=take_profit_str,
    )
    if resp.get("retCode") != 0:
        raise ValueError(f"{symbol} emri gonderilemedi: {resp.get('retMsg')}")
    logger.info(
        "%s %s qty=%s @ ~%s SL=%s TP=%s emri gonderildi (yeni kademe eklendi)",
        symbol, side, qty_str, f"{price:.{price_decimals}f}", stop_loss_str, take_profit_str,
    )
    return resp


def close_position(symbol: str, category: str = None) -> dict:
    """Acik pozisyonu (varsa) piyasa emriyle kapatir."""
    category = category or config.CRYPTO_CATEGORY
    position = get_open_position(symbol, category=category)
    if position is None:
        logger.info("%s icin acik pozisyon yok, kapatilacak bir sey yok", symbol)
        return {"skipped": True, "reason": "no_position"}

    close_side = "Sell" if position["side"] == "Buy" else "Buy"
    qty = position["size"]

    if not config.CRYPTO_AUTO_TRADE_ENABLED:
        logger.info(
            "[DRY-RUN] %s %s qty=%s pozisyonu kapatilacakti (CRYPTO_AUTO_TRADE_ENABLED=False, emir gonderilmedi)",
            symbol, close_side, qty,
        )
        return {"dry_run": True, "symbol": symbol, "side": close_side, "qty": qty}

    _assert_safe_to_trade()
    resp = _client().place_order(
        category=category,
        symbol=symbol,
        side=close_side,
        orderType="Market",
        qty=str(qty),
        reduceOnly=True,
    )
    if resp.get("retCode") != 0:
        raise ValueError(f"{symbol} pozisyonu kapatilamadi: {resp.get('retMsg')}")
    logger.info("%s pozisyonu kapatildi (qty=%s)", symbol, qty)
    return resp
