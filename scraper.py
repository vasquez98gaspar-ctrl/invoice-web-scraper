"""
scraper.py — Logs into the portal and extracts today's orders + tracking numbers.
"""

import logging
import time
from datetime import date
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup
import requests
import config

logger = logging.getLogger(__name__)


@dataclass
class Order:
    order_number: str
    tracking_number: str
    order_date: str
    status: str = "—"
    tracking_url: Optional[str] = None


class StaticScraper:
    def __init__(self):
        self.session = requests.Session()

    def login(self) -> bool:
        return False

    def _parse_orders(self, html: str) -> list[Order]:
        soup = BeautifulSoup(html, "html.parser")
        today_str = date.today().strftime("%m/%d/%y")
        orders: list[Order] = []

        # Order rows have no class and contain td.rp-section-header--name
        all_trs = list(soup.find_all("tr"))
        all_rows = [(i, tr) for i, tr in enumerate(all_trs) if tr.select_one("td.rp-section-header--name")]
        # Only keep rows that have a valid inner table (skip duplicates)
        rows = [(i, tr) for i, tr in all_rows if tr.select_one("td.rp-accordion-section table.tbl-main-header")]
        all_trs_list = all_trs
        # Build stop indices using ALL order row indices (including duplicates)
        all_order_indices = [i for i, _ in all_rows]
        logger.info("Found %d order row(s) to inspect.", len(rows))

        def cell_value(td):
            """Get the text value from a cell — skips the label, returns the direct text node."""
            if not td:
                return "—"
            import copy
            td = copy.copy(td)
            label = td.find("label")
            if label:
                label.decompose()
            return td.get_text(strip=True)

        seen = set()
        for row_idx, row in rows:
            inner_tr = row.select_one("td.rp-accordion-section table.tbl-main-header tr")
            if not inner_tr:
                continue

            name_td   = inner_tr.select_one("td.rp-section-header--name")
            conf_td   = inner_tr.select_one("td.rp-section-header--confirmation")
            date_td   = inner_tr.select_one("td.rp-section-header--date")
            status_td = inner_tr.select_one("td.rp-section-header--status")

            if not name_td:
                continue

            order_num  = cell_value(name_td)
            conf_num   = cell_value(conf_td)
            order_date = cell_value(date_td)
            status     = cell_value(status_td)

            if not order_num or order_num in seen:
                continue
            seen.add(order_num)

            if config.FILTER_TODAY_ONLY and today_str not in order_date:
                continue

            # Grab tracking numbers from rows that follow this order row
            # until we hit the next order row
            tracking_numbers = []
            # Use all order row indices (including duplicates) to find stop point
            next_order_indices = [i for i in all_order_indices if i > row_idx]
            # Skip the immediate duplicate (next index), use the one after
            stop_idx = next_order_indices[1] if len(next_order_indices) > 1 else (next_order_indices[0] if next_order_indices else len(all_trs_list))

            for detail_tr in all_trs_list[row_idx + 1 : stop_idx]:
                for track_td in detail_tr.select("td.rp-track-no-area"):
                    val = track_td.get_text(strip=True)
                    if val and val.upper() not in ("N/A", "TRACK NO", "TRACK NO.", "", "CANCEL ITEM"):
                        tracking_numbers.append(val)

            tracking_str = ", ".join(dict.fromkeys(tracking_numbers)) if tracking_numbers else conf_num

            orders.append(Order(
                order_number    = order_num,
                tracking_number = tracking_str,
                order_date      = order_date,
                status          = status,
                tracking_url    = None,
            ))

        logger.info("Parsed %d order(s).", len(orders))
        return orders


class SeleniumScraper:
    def __init__(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        opts = Options()
        # opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.driver.set_page_load_timeout(30)

    def login(self) -> bool:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        logger.info("Navigating to login page (Selenium).")
        self.driver.get(config.LOGIN_URL)

        try:
            wait = WebDriverWait(self.driver, 20)

            # Wait for username input to be present
            logger.info("Waiting for login form...")
            username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='userID']")))
            time.sleep(2)

            # Set username via native JS setter (bypasses Angular binding)
            self.driver.execute_script("""
                var el = arguments[0];
                var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, arguments[1]);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            """, username_field, config.PORTAL_USERNAME)
            time.sleep(0.5)

            # Click password field and paste via clipboard
            password_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']")))
            password_field.click()
            time.sleep(0.5)

            # Copy password to clipboard and paste
            try:
                import pyperclip
                pyperclip.copy(config.PORTAL_PASSWORD)
            except ImportError:
                pass

            password_field.send_keys(Keys.CONTROL, 'a')
            time.sleep(0.2)
            password_field.send_keys(Keys.CONTROL, 'v')
            time.sleep(0.5)

            # Submit with Enter
            password_field.send_keys(Keys.RETURN)
            logger.info("Submitted login, waiting for redirect...")

            # Wait for redirect away from login
            wait.until(lambda d: "login" not in d.current_url.split("#")[-1])
            time.sleep(3)

            current_url = self.driver.current_url
            logger.info("Current URL after login: %s", current_url)
            logger.info("Selenium login successful.")
            return True

        except Exception as exc:
            current_url = self.driver.current_url
            logger.error("Selenium login failed: %s", exc)
            logger.error("Current URL: %s", current_url)
            return False

    def fetch_orders(self) -> list[Order]:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        logger.info("Navigating to orders page (Selenium).")
        self.driver.get(config.ORDERS_URL)
        logger.info("Waiting for orders to render...")

        try:
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tr.rp-accordion--header"))
            )
            logger.info("Orders table found in DOM.")
            time.sleep(2)

            # Click "Expand All" to reveal tracking numbers in detail rows
            try:
                expand_btn = self.driver.find_element(By.CSS_SELECTOR, ".rp-accordion--header-expand span")
                self.driver.execute_script("arguments[0].click();", expand_btn)
                logger.info("Clicked Expand All.")
                time.sleep(4)  # Wait for all rows to expand
            except Exception as e:
                logger.warning("Could not click Expand All: %s", e)

        except Exception:
            logger.warning("Timed out waiting for order table — parsing whatever loaded.")

        html = self.driver.page_source

        with open("debug_orders_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Saved debug snapshot to debug_orders_page.html")

        self.driver.quit()

        static = StaticScraper()
        return static._parse_orders(html)


def get_orders() -> list[Order]:
    ScraperClass = SeleniumScraper if config.USE_SELENIUM else StaticScraper
    scraper = ScraperClass()

    if not scraper.login():
        raise RuntimeError("Could not log in to the portal. Check credentials and LOGIN_URL.")

    return scraper.fetch_orders()
