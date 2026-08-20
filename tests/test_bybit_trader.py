import pytest

import bybit_trader
import config


class FakeClient:
    def __init__(
        self,
        balance=1000.0,
        instrument=None,
        position=None,
        leverage_ret_code=0,
        place_order_ret_code=0,
    ):
        self.balance = balance
        self.instrument = instrument or {
            "lotSizeFilter": {"qtyStep": "0.001", "minOrderQty": "0.001"}
        }
        self.position = position
        self.leverage_ret_code = leverage_ret_code
        self.place_order_ret_code = place_order_ret_code
        self.place_order_calls = []
        self.set_leverage_calls = []

    def get_wallet_balance(self, accountType, coin):
        return {
            "retCode": 0,
            "result": {"list": [{"coin": [{"coin": "USDT", "walletBalance": str(self.balance)}]}]},
        }

    def get_instruments_info(self, category, symbol):
        return {"retCode": 0, "result": {"list": [self.instrument]}}

    def get_positions(self, category, symbol):
        return {"retCode": 0, "result": {"list": [self.position] if self.position else []}}

    def set_leverage(self, category, symbol, buyLeverage, sellLeverage):
        self.set_leverage_calls.append((symbol, buyLeverage, sellLeverage))
        return {"retCode": self.leverage_ret_code, "retMsg": "leverage not modified"}

    def place_order(self, **kwargs):
        self.place_order_calls.append(kwargs)
        return {"retCode": self.place_order_ret_code, "retMsg": "OK", "result": {"orderId": "123"}}


@pytest.fixture(autouse=True)
def _reset_config(monkeypatch):
    monkeypatch.setattr(config, "BYBIT_TESTNET", True)
    monkeypatch.setattr(config, "CONFIRM_LIVE_TRADING", False)
    monkeypatch.setattr(config, "CRYPTO_AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr(config, "CRYPTO_POSITION_SIZE_PCT", 5.0)
    monkeypatch.setattr(config, "CRYPTO_LEVERAGE", 3)
    monkeypatch.setattr(config, "CRYPTO_STOP_LOSS_PCT", 3.0)
    monkeypatch.setattr(config, "CRYPTO_TAKE_PROFIT_PCT", 6.0)


def test_round_qty_floors_to_step():
    assert bybit_trader.round_qty(0.12345, qty_step=0.001, min_qty=0.001) == 0.123


def test_round_qty_returns_zero_below_minimum():
    assert bybit_trader.round_qty(0.0005, qty_step=0.001, min_qty=0.001) == 0.0


def test_calculate_position_qty(monkeypatch):
    fake = FakeClient(balance=1000.0)
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    # balance=1000, pct=5% -> 50, leverage=3 -> notional=150, price=100 -> qty=1.5
    qty = bybit_trader.calculate_position_qty("BTCUSDT", price=100.0, balance=1000.0)

    assert qty == 1.5


def test_open_position_dry_run_does_not_call_place_order(monkeypatch):
    monkeypatch.setattr(config, "CRYPTO_AUTO_TRADE_ENABLED", False)
    fake = FakeClient(balance=1000.0)
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    result = bybit_trader.open_position("BTCUSDT", "Buy", price=100.0)

    assert result["dry_run"] is True
    assert fake.place_order_calls == []


def test_open_position_skips_when_position_already_open(monkeypatch):
    fake = FakeClient(balance=1000.0, position={"side": "Buy", "size": "1.0"})
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    result = bybit_trader.open_position("BTCUSDT", "Buy", price=100.0)

    assert result == {"skipped": True, "reason": "position_exists"}
    assert fake.place_order_calls == []


def test_open_position_skips_when_qty_too_small(monkeypatch):
    fake = FakeClient(
        balance=0.01,
        instrument={"lotSizeFilter": {"qtyStep": "0.001", "minOrderQty": "0.001"}},
    )
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    result = bybit_trader.open_position("BTCUSDT", "Buy", price=100000.0)

    assert result == {"skipped": True, "reason": "qty_too_small"}
    assert fake.place_order_calls == []


def test_open_position_places_market_order_with_sl_tp_on_testnet(monkeypatch):
    # leverage=3, STOP_LOSS_PCT=3.0 (pozisyon %) -> fiyat hareketi 3/3=%1
    # leverage=3, TAKE_PROFIT_PCT=6.0 (pozisyon %) -> fiyat hareketi 6/3=%2
    fake = FakeClient(balance=1000.0)
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    bybit_trader.open_position("BTCUSDT", "Buy", price=100.0)

    assert len(fake.place_order_calls) == 1
    call = fake.place_order_calls[0]
    assert call["side"] == "Buy"
    assert call["orderType"] == "Market"
    assert float(call["stopLoss"]) == pytest.approx(99.0)
    assert float(call["takeProfit"]) == pytest.approx(102.0)


def test_open_position_sl_tp_scales_with_leverage(monkeypatch):
    # leverage=20, STOP_LOSS_PCT=25 (pozisyon %) -> fiyat hareketi 25/20=%1.25
    monkeypatch.setattr(config, "CRYPTO_LEVERAGE", 20)
    monkeypatch.setattr(config, "CRYPTO_STOP_LOSS_PCT", 25.0)
    monkeypatch.setattr(config, "CRYPTO_TAKE_PROFIT_PCT", 25.0)
    fake = FakeClient(balance=1000.0)
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    bybit_trader.open_position("BTCUSDT", "Buy", price=100.0)

    call = fake.place_order_calls[0]
    assert float(call["stopLoss"]) == pytest.approx(98.75)
    assert float(call["takeProfit"]) == pytest.approx(101.25)


def test_open_position_refuses_on_mainnet_without_confirmation(monkeypatch):
    monkeypatch.setattr(config, "BYBIT_TESTNET", False)
    monkeypatch.setattr(config, "CONFIRM_LIVE_TRADING", False)
    fake = FakeClient(balance=1000.0)
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    with pytest.raises(RuntimeError):
        bybit_trader.open_position("BTCUSDT", "Buy", price=100.0)

    assert fake.place_order_calls == []


def test_open_position_allowed_on_mainnet_with_confirmation(monkeypatch):
    monkeypatch.setattr(config, "BYBIT_TESTNET", False)
    monkeypatch.setattr(config, "CONFIRM_LIVE_TRADING", True)
    fake = FakeClient(balance=1000.0)
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    result = bybit_trader.open_position("BTCUSDT", "Buy", price=100.0)

    assert result["retCode"] == 0
    assert len(fake.place_order_calls) == 1


def test_close_position_skips_when_no_position(monkeypatch):
    fake = FakeClient(balance=1000.0, position=None)
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    result = bybit_trader.close_position("BTCUSDT")

    assert result == {"skipped": True, "reason": "no_position"}


def test_close_position_dry_run(monkeypatch):
    monkeypatch.setattr(config, "CRYPTO_AUTO_TRADE_ENABLED", False)
    fake = FakeClient(balance=1000.0, position={"side": "Buy", "size": "1.0"})
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    result = bybit_trader.close_position("BTCUSDT")

    assert result["dry_run"] is True
    assert fake.place_order_calls == []


def test_close_position_places_reduce_only_opposite_side_order(monkeypatch):
    fake = FakeClient(balance=1000.0, position={"side": "Buy", "size": "1.0"})
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    bybit_trader.close_position("BTCUSDT")

    assert len(fake.place_order_calls) == 1
    call = fake.place_order_calls[0]
    assert call["side"] == "Sell"
    assert call["reduceOnly"] is True
    assert call["qty"] == "1.0"


def test_set_leverage_treats_not_modified_as_success(monkeypatch):
    fake = FakeClient(leverage_ret_code=110043)
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    bybit_trader.set_leverage("BTCUSDT")  # should not raise


def test_set_leverage_raises_on_real_error(monkeypatch):
    fake = FakeClient(leverage_ret_code=99999)
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    with pytest.raises(ValueError):
        bybit_trader.set_leverage("BTCUSDT")


def test_set_leverage_formats_whole_numbers_without_decimal(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(bybit_trader, "_client", lambda: fake)

    bybit_trader.set_leverage("BTCUSDT", leverage=20.0)

    assert fake.set_leverage_calls == [("BTCUSDT", "20", "20")]
