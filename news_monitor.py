from datetime import date, timedelta

import requests

FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/company-news"

# Basit onem filtresi icin anahtar kelimeler (baslik/ozet icinde aranir)
SIGNIFICANT_KEYWORDS = [
    "earnings", "guidance", "downgrade", "upgrade", "lawsuit", "sec ",
    "investigation", "recall", "ceo", "acquisition", "merger", "bankruptcy",
    "fda", "buyback", "dividend", "layoff", "resign",
]


def get_recent_news(symbol: str, api_key: str, days: int = 7, limit: int = 5) -> list:
    """Finnhub uzerinden sirket haberlerini ceker. Tarih araligi bugune gore dinamiktir."""
    if not api_key:
        raise ValueError("NEWS_API_KEY ayarlanmamis")

    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    params = {
        "symbol": symbol,
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "token": api_key,
    }
    resp = requests.get(FINNHUB_NEWS_URL, params=params, timeout=10)
    resp.raise_for_status()
    articles = resp.json()
    return articles[:limit]


def filter_significant(articles: list) -> list:
    """Baslik veya ozetinde onemli bir anahtar kelime gecen haberleri dondurur."""
    significant = []
    for article in articles:
        text = f"{article.get('headline', '')} {article.get('summary', '')}".lower()
        if any(keyword in text for keyword in SIGNIFICANT_KEYWORDS):
            significant.append(article)
    return significant
