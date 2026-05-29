# Automated Order & Tracking Report System
### Project Case Study — Built with Python, Selenium & Gmail SMTP

---

## Overview

A fully automated web scraper that logs into a supplier portal (ReliableParts.net), extracts daily orders with real UPS/FedEx carrier tracking numbers, and delivers a formatted HTML email report — built from scratch without any third-party APIs or paid services.

**Tech Stack:** Python 3 · Selenium · ChromeDriver · BeautifulSoup4 · Gmail SMTP · Raspberry Pi (planned)

---

## Problem Solved

Orders placed through ReliableParts.net required manual daily review — logging in, expanding each order row, and copying confirmation and tracking numbers one by one. This system eliminates that process entirely with a scheduled daily report delivered automatically to any inbox.

---

## Key Technical Challenges Overcome

| Challenge | Solution |
|---|---|
| **Angular SPA authentication** | Portal uses an Angular app with a `wz-mask` input library that blocks standard automation. Bypassed using a native `HTMLInputElement` value setter via JavaScript injection, combined with clipboard-paste for the password field. |
| **Dynamic nested HTML structure** | Orders render in a duplicated accordion structure with tracking numbers hidden in lazily-loaded expandable rows. Solved by clicking "Expand All" before capture, then using index-based row slicing to associate each tracking number with its parent order. |
| **Professional HTML email** | Outputs a styled email with color-coded status badges (Invoiced, Backordered, In Process), real carrier tracking numbers, and a plain-text fallback — via Gmail SMTP, no third-party service required. |

---

## Results

| Metric | Value |
|---|---|
| Orders parsed per run | 20+ |
| End-to-end runtime | ~30 seconds |
| Manual steps required | 0 |

---

## Project Architecture

```
order_scraper/
├── config.py       ← All settings: URLs, credentials, CSS selectors, email config
├── scraper.py      ← Login + Selenium automation + HTML parsing
├── emailer.py      ← HTML email builder + Gmail SMTP sender
├── main.py         ← Entry point (--dry-run, --test-email flags)
└── requirements.txt
```

**Two scraper modes:**
- `StaticScraper` — requests + BeautifulSoup for standard pages
- `SeleniumScraper` — headless Chrome for JavaScript-rendered portals (used here)

---

## Core Scraper Logic

```python
# ── Login: bypass Angular wz-mask input library ──────────────────────────────

# Standard send_keys() fails on masked inputs.
# Solution: use the native HTMLInputElement setter to trigger Angular's change detection.

driver.execute_script("""
    var el = arguments[0];
    var setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
    ).set;
    setter.call(el, arguments[1]);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
""", username_field, config.PORTAL_USERNAME)

# Password field uses clipboard paste to bypass the mask
import pyperclip
pyperclip.copy(config.PORTAL_PASSWORD)
password_field.send_keys(Keys.CONTROL, 'v')
password_field.send_keys(Keys.RETURN)
```

```python
# ── Expand all order rows before scraping ────────────────────────────────────

# Tracking numbers only appear in expanded accordion rows.
# Click "Expand All" then wait for DOM to settle.

WebDriverWait(driver, 60).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "tr.rp-accordion--header"))
)
expand_btn = driver.find_element(By.CSS_SELECTOR, ".rp-accordion--header-expand span")
driver.execute_script("arguments[0].click();", expand_btn)
time.sleep(4)  # Let all rows expand
```

```python
# ── Parse orders + match tracking numbers ────────────────────────────────────

# The page renders each order row TWICE (a known Angular duplication).
# Tracking detail rows sit between the duplicate pairs.
# Solution: index all rows, skip duplicates, slice between pairs to find tracking.

all_trs = list(soup.find_all("tr"))
all_rows = [(i, tr) for i, tr in enumerate(all_trs)
            if tr.select_one("td.rp-section-header--name")]
rows = [(i, tr) for i, tr in all_rows
        if tr.select_one("td.rp-accordion-section table.tbl-main-header")]
all_order_indices = [i for i, _ in all_rows]

for row_idx, row in rows:
    # Find the slice of rows that belong to this order
    next_indices = [i for i in all_order_indices if i > row_idx]
    stop_idx = next_indices[1] if len(next_indices) > 1 else len(all_trs)

    tracking_numbers = []
    for detail_tr in all_trs[row_idx + 1 : stop_idx]:
        for track_td in detail_tr.select("td.rp-track-no-area"):
            val = track_td.get_text(strip=True)
            if val and val.upper() not in ("N/A", "TRACK NO", "", "CANCEL ITEM"):
                tracking_numbers.append(val)

    tracking_str = ", ".join(dict.fromkeys(tracking_numbers)) if tracking_numbers else conf_num
    print(f"Order {order_num}: {tracking_str}")
```

---

## Sample Output

The script prints a summary to the terminal and sends an HTML email:

```
Order #         Tracking #                Date        Status
─────────────────────────────────────────────────────────────────────────
2129477         3748350                   05/22/26    Order in Process
2129405         1Z7524310318504417        05/22/26    Invoiced
2129036         1Z8916130302721477        05/22/26    Invoiced
2129014         1Z7AT3880308782216        05/22/26    Backordered
2128822         1Z1R02R30303499232        05/22/26    Invoiced
2127870         1Z7AT3880308781600        05/22/26    Invoiced
...
```

The HTML email includes color-coded status badges:
- 🟢 **Invoiced** — green
- 🟡 **Backordered / Pending** — yellow  
- 🔴 **Cancelled / Error** — red
- ⚪ **Order in Process** — gray

---

## Deployment Plan

Currently running manually. Planned deployment on a **Raspberry Pi** connected to a home router for 24/7 autonomous operation:

```bash
# cron job — runs at 6 PM daily
0 18 * * * cd /home/pi/order_scraper && python3 main.py >> /tmp/orders.log 2>&1
```

---

## Future Enhancements

- Filter to today's orders only (date-range query parameter)
- Clickable UPS/FedEx tracking links in the email
- Support for multiple supplier portals
- Slack/Teams notification integration
- Exception alerts when orders are backordered

---
*Built independently — May 2026*
