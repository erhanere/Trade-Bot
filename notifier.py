import logging

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Telegram uzerinden mesaj gonderir. Basarili olursa True, olmazsa False dondurur."""
    if not token or not chat_id:
        logger.warning("Telegram token/chat_id ayarlanmamis, bildirim gonderilmedi: %s", text)
        return False

    url = TELEGRAM_API_URL.format(token=token)
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Telegram bildirimi gonderilemedi")
        return False
