"""
emailer.py — Builds a polished HTML email and sends it via Gmail SMTP.
"""

import smtplib
import logging
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
from scraper import Order

logger = logging.getLogger(__name__)

# =============================================================================
#  HTML builder
# =============================================================================

def build_html(orders: list[Order], report_date: str) -> str:
    """Return a complete HTML email body with a styled orders table."""

    if orders:
        rows_html = ""
        for i, order in enumerate(orders):
            bg = "#ffffff" if i % 2 == 0 else "#f7f9fc"

            # Make tracking number a link if we have a URL
            if order.tracking_url:
                tracking_cell = (
                    f'<a href="{order.tracking_url}" '
                    f'style="color:#2563eb;text-decoration:none;font-weight:600;">'
                    f'{order.tracking_number}</a>'
                )
            else:
                tracking_cell = f'<strong>{order.tracking_number}</strong>'

            rows_html += f"""
            <tr style="background:{bg};">
              <td style="{TD}">{order.order_number}</td>
              <td style="{TD}">{tracking_cell}</td>
              <td style="{TD}">{order.order_date}</td>
              <td style="{TD}">
                <span style="{status_badge(order.status)}">{order.status}</span>
              </td>
            </tr>"""

        table_html = f"""
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="border-collapse:collapse;border-radius:8px;overflow:hidden;
                      box-shadow:0 1px 4px rgba(0,0,0,0.08);">
          <thead>
            <tr style="background:#1e3a5f;color:#ffffff;">
              <th style="{TH}">Order #</th>
              <th style="{TH}">Tracking Number</th>
              <th style="{TH}">Date</th>
              <th style="{TH}">Status</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>"""

        summary = (
            f'<p style="margin:0 0 24px;color:#374151;font-size:15px;">'
            f'<strong>{len(orders)}</strong> order(s) processed for <strong>{report_date}</strong>.</p>'
        )
    else:
        table_html = (
            '<p style="text-align:center;padding:32px;color:#6b7280;font-size:15px;">'
            'No orders found for today.</p>'
        )
        summary = ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Daily Order Report</title>
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f0f4f8;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="680" cellpadding="0" cellspacing="0" border="0"
               style="max-width:680px;width:100%;background:#ffffff;border-radius:12px;
                      box-shadow:0 2px 12px rgba(0,0,0,0.10);overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
                        padding:32px 40px;">
              <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.3px;">
                📦 Daily Order &amp; Tracking Report
              </h1>
              <p style="margin:6px 0 0;color:#bfdbfe;font-size:14px;">{report_date}</p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 40px;">
              {summary}
              {table_html}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 40px;background:#f8fafc;border-top:1px solid #e5e7eb;">
              <p style="margin:0;color:#9ca3af;font-size:12px;text-align:center;">
                Generated automatically by Order Scraper &nbsp;·&nbsp; {report_date}
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


# =============================================================================
#  Style helpers
# =============================================================================

TH = (
    "padding:12px 16px;text-align:left;font-size:13px;"
    "font-weight:600;letter-spacing:0.4px;text-transform:uppercase;"
)

TD = (
    "padding:12px 16px;font-size:14px;color:#1f2937;"
    "border-bottom:1px solid #f3f4f6;"
)


def status_badge(status: str) -> str:
    s = status.lower()
    if any(w in s for w in ("delivered", "complete", "shipped")):
        return "background:#d1fae5;color:#065f46;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;"
    if any(w in s for w in ("pending", "processing")):
        return "background:#fef3c7;color:#92400e;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;"
    if any(w in s for w in ("cancel", "error", "fail")):
        return "background:#fee2e2;color:#991b1b;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;"
    return "background:#e5e7eb;color:#374151;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;"


# =============================================================================
#  Send
# =============================================================================

def send_report(orders: list[Order]) -> None:
    report_date = date.today().strftime("%B %d, %Y")
    subject     = config.EMAIL_SUBJECT.format(date=report_date)
    html_body   = build_html(orders, report_date)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = config.GMAIL_SENDER
    msg["To"]      = ", ".join(config.EMAIL_RECIPIENTS)

    # Plain-text fallback
    plain = f"Daily Order Report — {report_date}\n\n"
    for o in orders:
        plain += f"Order: {o.order_number}  |  Tracking: {o.tracking_number}  |  Date: {o.order_date}  |  Status: {o.status}\n"
    if not orders:
        plain += "No orders found for today.\n"

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    logger.info("Connecting to Gmail SMTP...")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config.GMAIL_SENDER, config.GMAIL_APP_PASSWORD)
            server.sendmail(
                config.GMAIL_SENDER,
                config.EMAIL_RECIPIENTS,
                msg.as_string(),
            )
        logger.info("Email sent to: %s", ", ".join(config.EMAIL_RECIPIENTS))
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail authentication failed.\n"
            "Make sure you're using an App Password, not your regular Gmail password.\n"
            "Generate one at: https://myaccount.google.com/apppasswords"
        )
        raise
    except smtplib.SMTPException as exc:
        logger.error("Failed to send email: %s", exc)
        raise
