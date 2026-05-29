# =============================================================================
#  config.py — Edit ALL values in this file before running
# =============================================================================

# --- Portal Settings ---------------------------------------------------------
PORTAL_URL        = "https://your-portal.com"          # Base URL of the portal
LOGIN_URL         = "https://your-portal.com/login"    # Login page URL
ORDERS_URL        = "https://your-portal.com/orders"   # Page that lists today's orders

PORTAL_USERNAME   = "your_username"
PORTAL_PASSWORD   = "your_password"

# HTML field names for the login form (inspect the page source to find these)
USERNAME_FIELD    = "username"   # e.g. name="username"
PASSWORD_FIELD    = "password"   # e.g. name="password"

# --- CSS Selectors -----------------------------------------------------------
# Inspect your orders page and update these selectors to match its structure.
# Tip: Right-click an element → "Inspect" → copy the CSS selector.

ORDER_ROW_SELECTOR     = "table tbody tr"   # Each row in the orders table
ORDER_NUMBER_SELECTOR  = "td:nth-child(1)"  # Column containing the order #
TRACKING_SELECTOR      = "td:nth-child(2)"  # Column containing the tracking #
DATE_SELECTOR          = "td:nth-child(3)"  # Column containing the date
STATUS_SELECTOR        = "td:nth-child(4)"  # Column containing the status (optional)

# --- Email Settings ----------------------------------------------------------
GMAIL_SENDER      = "you@gmail.com"
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"  # Gmail App Password (not your regular password)
                                             # Generate one at: myaccount.google.com/apppasswords

EMAIL_RECIPIENTS  = [
    "recipient1@example.com",
    # "recipient2@example.com",  # Add more as needed
]

EMAIL_SUBJECT     = "Daily Order & Tracking Report — {date}"  # {date} is auto-filled

# --- Behavior Settings -------------------------------------------------------
# Filter orders to only today's date? Set False to grab ALL orders on the page.
FILTER_TODAY_ONLY = True

# If the portal uses JavaScript to render orders, set this to True.
# Requires: pip install selenium and ChromeDriverinstalled.
USE_SELENIUM      = False

# Path to ChromeDriver (only needed if USE_SELENIUM = True)
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
