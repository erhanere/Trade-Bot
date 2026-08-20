import notifier


class FakeResponse:
    def raise_for_status(self):
        pass


def test_returns_false_and_skips_request_without_credentials(monkeypatch):
    called = False

    def fake_post(*args, **kwargs):
        nonlocal called
        called = True
        return FakeResponse()

    monkeypatch.setattr(notifier.requests, "post", fake_post)

    result = notifier.send_telegram_message(None, None, "hello")

    assert result is False
    assert called is False


def test_sends_message_with_expected_payload(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(notifier.requests, "post", fake_post)

    result = notifier.send_telegram_message("tok123", "chat456", "AAPL BUY sinyali")

    assert result is True
    assert captured["url"] == "https://api.telegram.org/bottok123/sendMessage"
    assert captured["json"] == {"chat_id": "chat456", "text": "AAPL BUY sinyali"}


def test_returns_false_on_request_exception(monkeypatch):
    def fake_post(*args, **kwargs):
        raise notifier.requests.RequestException("network error")

    monkeypatch.setattr(notifier.requests, "post", fake_post)

    result = notifier.send_telegram_message("tok123", "chat456", "hello")

    assert result is False
