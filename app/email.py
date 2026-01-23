"""
Email service using Resend.

Features:
- Sends personalized welcome emails to new waitlist signups
- Comprehensive failure logging
- Serverless-compatible (no in-memory state)

Note: Rate limiting is handled by Resend's API limits.
For stricter control, consider Upstash Redis.
"""

import logging
import os

import resend

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Waitlist <onboarding@resend.dev>")


def send_welcome_email(to_email: str, first_name: str = "there") -> bool:
    """
    Send a personalized welcome email to a new waitlist signup.

    Args:
        to_email: Recipient email address
        first_name: User's first name for personalization

    Returns:
        True if email sent successfully, False otherwise
    """
    # Check if Resend is configured
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping email to %s", to_email)
        return False

    # Configure Resend
    resend.api_key = RESEND_API_KEY

    # Email content (personalized)
    subject = f"Welcome to the Waitlist, {first_name}! 🎉"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ font-size: 24px; font-weight: bold; margin-bottom: 20px; color: #1a1a1a; }}
            .content {{ margin-bottom: 20px; }}
            .highlight {{ background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .footer {{ font-size: 12px; color: #666; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">Hey {first_name}, You're In! 🎊</div>
        <div class="content">
            <p>Thanks for signing up for our waitlist! We're thrilled to have you.</p>
            <div class="highlight">
                <strong>What happens next?</strong><br>
                We'll notify you as soon as it's your turn to get access. Stay tuned!
            </div>
            <p>In the meantime, keep an eye on your inbox for updates and early access opportunities.</p>
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
