import pytest

import news_monitor


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_get_recent_news_raises_without_api_key():
    with pytest.raises(ValueError):
        news_monitor.get_recent_news("AAPL", api_key=None)


def test_get_recent_news_returns_limited_articles(monkeypatch):
    articles = [{"headline": f"News {i}"} for i in range(10)]

    def fake_get(url, params, timeout):
        assert params["symbol"] == "AAPL"
        assert params["token"] == "fake-key"
        assert "from" in params and "to" in params
        return FakeResponse(articles)

    monkeypatch.setattr(news_monitor.requests, "get", fake_get)

    result = news_monitor.get_recent_news("AAPL", api_key="fake-key", limit=3)

    assert len(result) == 3
    assert result[0]["headline"] == "News 0"


def test_filter_significant_matches_keywords():
    articles = [
        {"headline": "Company X announces earnings beat", "summary": ""},
        {"headline": "Analyst has coffee", "summary": "Nothing important happened today"},
        {"headline": "Regulator opens investigation into Company Y", "summary": ""},
    ]

    result = news_monitor.filter_significant(articles)

    assert len(result) == 2
    assert "earnings" in result[0]["headline"].lower()
