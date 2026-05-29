"""
main.py — Run this script to scrape orders and send the daily email.

Usage:
    python main.py               # Scrape + email
    python main.py --dry-run     # Scrape only, print results, no email sent
    python main.py --test-email  # Send a test email with sample data
"""

import argparse
import logging
import sys
from datetime import date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Daily order scraper & emailer")
    parser.add_argument("--dry-run",     action="store_true", help="Scrape only; don't send email")
    parser.add_argument("--test-email",  action="store_true", help="Send a test email with dummy data")
    args = parser.parse_args()

    # ── Test email mode ──────────────────────────────────────────────────────
    if args.test_email:
        logger.info("Sending test email with sample data...")
        from scraper import Order
        from emailer import send_report

        sample_orders = [
            Order("ORD-1001", "1Z999AA10123456784", date.today().isoformat(), "Shipped",
                  "https://www.ups.com/track?tracknum=1Z999AA10123456784"),
            Order("ORD-1002", "9400111899223397858482", date.today().isoformat(), "Delivered"),
            Order("ORD-1003", "420221539361289878901246316",  date.today().isoformat(), "Pending"),
        ]
        send_report(sample_orders)
        logger.info("Test email sent successfully.")
        return

    # ── Normal / dry-run mode ────────────────────────────────────────────────
    logger.info("=" * 55)
    logger.info("  Order Scraper — %s", date.today().strftime("%B %d, %Y"))
    logger.info("=" * 55)

    try:
        from scraper import get_orders
        orders = get_orders()
    except RuntimeError as exc:
        logger.error("Scraping failed: %s", exc)
        sys.exit(1)

    if not orders:
        logger.warning("No orders found for today. An empty report will be emailed.")

    # Pretty-print to console
    logger.info("\n  %-15s  %-30s  %-12s  %s", "Order #", "Tracking #", "Date", "Status")
    logger.info("  " + "-" * 75)
    for o in orders:
        logger.info("  %-15s  %-30s  %-12s  %s",
                    o.order_number, o.tracking_number, o.order_date, o.status)

    if args.dry_run:
        logger.info("\n[Dry run] Email NOT sent.")
        return

    # Send the report
    from emailer import send_report
    send_report(orders)
    logger.info("Done ✓")


if __name__ == "__main__":
    main()
