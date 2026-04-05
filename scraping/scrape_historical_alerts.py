"""
Scrape historical Tzeva Adom alert data from https://www.tzevaadom.co.il/en/historical/
Outputs: historical_alerts.csv

Alert card structure:
  <a href="/en/alerts/{id}">
    <p class="font-bold ...">  → regions
    <p class="text-[#d50f02] ...">  → "X hours ago | DD/MM/YY (HH:MM - HH:MM)"
    <p class="text-[#383838] ...">  → comma-separated cities
  </a>
"""

import csv
import logging
import re
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OUTPUT_FILE = "scrapping/historical_alerts.csv"
BASE_URL = "https://www.tzevaadom.co.il/en/historical/?mode=2"
MONTHS_BACK = 3

# Matches the anchor tags wrapping each alert card
ALERT_SELECTOR = "a[href*='/en/alerts/']"

# Time string format: "4 hours ago | 16/03/26 (22:21 - 22:20)"
TIME_PATTERN = re.compile(r"\|\s*(\d{2}/\d{2}/\d{2})\s*\((\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\)")


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def set_date_range(driver: webdriver.Chrome, wait: WebDriverWait, date_from: str, date_to: str) -> None:
    """Fill date-range inputs and fire React change events."""
    inputs = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='date']"))
    )
    if len(inputs) < 2:
        log.warning("Less than 2 date inputs found — skipping date filter.")
        return

    for field, value in zip(inputs[:2], [date_from, date_to]):
        driver.execute_script("arguments[0].value = arguments[1];", field, value)
        for event in ("input", "change"):
            driver.execute_script(
                f"arguments[0].dispatchEvent(new Event('{event}', {{bubbles:true}}));", field
            )

    # Click submit/search button if present
    buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button.search-btn")
    if buttons:
        buttons[0].click()
        log.info("Clicked filter button.")


def scroll_to_load_all(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """Scroll until no new alert cards appear (handles infinite scroll)."""
    last_count = 0
    stale_rounds = 0

    while stale_rounds < 3:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            wait.until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ALERT_SELECTOR)) > last_count
            )
            last_count = len(driver.find_elements(By.CSS_SELECTOR, ALERT_SELECTOR))
            log.info("Loaded %d alert cards so far…", last_count)
            stale_rounds = 0
        except TimeoutException:
            stale_rounds += 1

    log.info("Scroll complete. Total alert cards: %d", last_count)


def parse_alert(card) -> dict | None:
    """Extract fields from a single alert <a> element."""
    try:
        paragraphs = card.find_elements(By.TAG_NAME, "p")
        if len(paragraphs) < 3:
            return None

        regions = paragraphs[0].text.strip()
        time_text = paragraphs[1].text.strip()
        cities = paragraphs[2].text.strip()

        alert_date, time_start, time_end = "", "", ""
        match = TIME_PATTERN.search(time_text)
        if match:
            alert_date = match.group(1)   # DD/MM/YY
            time_start = match.group(2)   # HH:MM
            time_end = match.group(3)     # HH:MM

        return {
            "alert_date": alert_date,
            "time_start": time_start,
            "time_end": time_end,
            "regions": regions,
            "cities": cities,
            "raw_text": card.text.replace("\n", " ").strip(),
        }
    except Exception as exc:
        log.warning("Failed to parse alert card: %s", exc)
        return None


def scrape() -> None:
    date_to = datetime.today()
    date_from = date_to - timedelta(days=MONTHS_BACK * 30)
    date_from_str = date_from.strftime("%Y-%m-%d")
    date_to_str = date_to.strftime("%Y-%m-%d")

    log.info("Scraping alerts from %s to %s", date_from_str, date_to_str)

    driver = build_driver()
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(BASE_URL)
        log.info("Page loaded.")

        # Wait for React to render at least one alert card
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ALERT_SELECTOR)))

        try:
            set_date_range(driver, wait, date_from_str, date_to_str)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ALERT_SELECTOR)))
        except TimeoutException:
            log.warning("Date filter setup timed out — proceeding with current page state.")

        scroll_to_load_all(driver, wait)

        cards = driver.find_elements(By.CSS_SELECTOR, ALERT_SELECTOR)
        log.info("Found %d alert cards.", len(cards))

        rows = [r for card in cards if (r := parse_alert(card)) is not None]
        log.info("Parsed %d valid records.", len(rows))

    finally:
        driver.quit()

    if not rows:
        log.warning("No records extracted. Inspect the page structure and update ALERT_SELECTOR.")
        return

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["alert_date", "time_start", "time_end", "regions", "cities", "raw_text"]
        )
        writer.writeheader()
        writer.writerows(rows)

    log.info("Saved %d records to %s", len(rows), OUTPUT_FILE)


if __name__ == "__main__":
    scrape()
