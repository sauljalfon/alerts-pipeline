import requests
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "Referer": "https://www.oref.org.il/",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

URL = "https://alerts-history.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx?lang=en&mode=1"

def _fetch_alerts(**context):
    logger.info("Fetching alerts from the oref endpoint")

    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()

    data = response.json()
    logger.info("Fetched %d alerts from the oref endpoint", len(data))

    return data