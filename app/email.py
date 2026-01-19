"""
Email service using Resend.

Features:
- Sends welcome emails to new waitlist signups
- Rate limiting (configurable daily limit, default 300)
- Comprehensive failure logging
"""

import logging
import os
from datetime import date
from threading import Lock

import resend

# Configure logging
logger = logging.getLogger(__name__)

# Rate limiting state (in-memory, resets on restart)
# For multi-instance deployments, consider using Redis or database
_rate_limit_lock = Lock()
_daily_count = 0
_current_date: date | None = None

# Configuration from environment
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
DAILY_EMAIL_LIMIT = int(os.getenv("DAILY_EMAIL_LIMIT", "300"))
EMAIL_FROM = os.getenv("EMAIL_FROM", "Waitlist <onboarding@resend.dev>")


def _check_and_increment_rate_limit() -> bool:
    """
    Check if we're under the daily limit and increment counter.
    Returns True if email can be sent, False if limit reached.
    Thread-safe.
    """
    global _daily_count, _current_date

    with _rate_limit_lock:
        today = date.today()

        # Reset counter if it's a new day
        if _current_date != today:
            _current_date = today
            _daily_count = 0

        if _daily_count >= DAILY_EMAIL_LIMIT:
            return False

        _daily_count += 1
        return True


def get_daily_email_count() -> int:
    """Return current daily email count (for monitoring)."""
    with _rate_limit_lock:
        today = date.today()
        if _current_date != today:
            return 0
        return _daily_count


def send_welcome_email(to_email: str) -> bool:
    """
    Send a welcome email to a new waitlist signup.

    Args:
        to_email: Recipient email address

    Returns:
        True if email sent successfully, False otherwise
    """
    # Check if Resend is configured
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping email to %s", to_email)
        return False

    # Check rate limit
    if not _check_and_increment_rate_limit():
        logger.warning(
            "Daily email limit (%d) reached, skipping email to %s",
            DAILY_EMAIL_LIMIT,
            to_email,
        )
        return False

    # Configure Resend
    resend.api_key = RESEND_API_KEY

    # Email content
    subject = "You're on the waitlist! 🎉"
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { font-size: 24px; font-weight: bold; margin-bottom: 20px; }
            .content { margin-bottom: 20px; }
            .footer { font-size: 12px; color: #666; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }
        </style>
    </head>
    <body>
        <div class="header">Welcome to the Waitlist!</div>
        <div class="content">
            <p>Thanks for signing up! We're excited to have you.</p>
            <p>You're now on our waitlist. We'll notify you as soon as it's your turn to get access.</p>
            <p>In the meantime, stay tuned for updates!</p>
        </div>
        <div class="footer">
            <p>You received this email because you signed up for our waitlist.</p>
        </div>
    </body>
    </html>
    """

    try:
        params: resend.Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        response = resend.Emails.send(params)
        logger.info("Email sent successfully to %s (id: %s)", to_email, response.get("id"))
        return True

    except resend.exceptions.ResendError as e:
        logger.error("Resend API error sending to %s: %s", to_email, str(e))
        return False
    except Exception as e:
        logger.error("Unexpected error sending email to %s: %s", to_email, str(e))
        return False
