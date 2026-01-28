"""
Email service using Resend.

Features:
- Sends personalized welcome emails to new waitlist signups
- Sends contact form notification emails to admin
- Comprehensive failure logging
- Serverless-compatible (no in-memory state)

Note: Rate limiting is handled by Resend's API limits.
For stricter control, consider Upstash Redis.
"""

import logging
import os
from html import escape

import resend

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = "Waitlist <onboarding@resend.dev>"

# Contact form notifications go to this address
# Set CONTACT_NOTIFY_EMAIL env var, or falls back to a default
CONTACT_NOTIFY_EMAIL = os.getenv("CONTACT_NOTIFY_EMAIL", "admin@example.com")


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


def send_contact_notification(
    sender_name: str,
    sender_email: str,
    subject: str,
    message: str,
    ip_address: str | None = None,
) -> bool:
    """
    Send a notification email when someone submits the contact form.

    Args:
        sender_name: Name of the person who submitted the form
        sender_email: Their email address (for reply)
        subject: Subject of their message
        message: The message content
        ip_address: Optional IP address for tracking

    Returns:
        True if email sent successfully, False otherwise
    """
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping contact notification")
        return False

    if not CONTACT_NOTIFY_EMAIL or CONTACT_NOTIFY_EMAIL == "admin@example.com":
        logger.warning("CONTACT_NOTIFY_EMAIL not configured, skipping contact notification")
        return False

    resend.api_key = RESEND_API_KEY

    # Escape HTML in user-provided content
    safe_name = escape(sender_name)
    safe_email = escape(sender_email)
    safe_subject = escape(subject)
    safe_message = escape(message).replace("\n", "<br>")
    safe_ip = escape(ip_address) if ip_address else "Unknown"

    email_subject = f"[Contact Form] {subject}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }}
            .header {{ font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #1a1a1a; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }}
            .meta {{ background: #f8fafc; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #3b82f6; }}
            .meta-row {{ margin: 8px 0; }}
            .meta-label {{ font-weight: 600; color: #64748b; display: inline-block; width: 80px; }}
            .message-box {{ background: #ffffff; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .message-content {{ white-space: pre-wrap; word-wrap: break-word; }}
            .footer {{ font-size: 12px; color: #94a3b8; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
            .reply-btn {{ display: inline-block; background: #3b82f6; color: #ffffff; padding: 10px 20px; border-radius: 6px; text-decoration: none; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="header">📬 New Contact Form Submission</div>
        
        <div class="meta">
            <div class="meta-row"><span class="meta-label">From:</span> {safe_name}</div>
            <div class="meta-row"><span class="meta-label">Email:</span> <a href="mailto:{safe_email}">{safe_email}</a></div>
            <div class="meta-row"><span class="meta-label">Subject:</span> {safe_subject}</div>
            <div class="meta-row"><span class="meta-label">IP:</span> {safe_ip}</div>
        </div>
        
        <div class="message-box">
            <div class="message-content">{safe_message}</div>
        </div>
        
        <a href="mailto:{safe_email}?subject=Re: {safe_subject}" class="reply-btn">Reply to {safe_name}</a>
        
        <div class="footer">
            <p>This message was sent via your website's contact form.</p>
        </div>
    </body>
    </html>
    """

    try:
        params: resend.Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [CONTACT_NOTIFY_EMAIL],
            "reply_to": sender_email,
            "subject": email_subject,
            "html": html_content,
        }

        response = resend.Emails.send(params)
        logger.info(
            "Contact notification sent (id: %s) from %s <%s>",
            response.get("id"),
            sender_name,
            sender_email,
        )
        return True

    except resend.exceptions.ResendError as e:
        logger.error("Resend API error for contact notification: %s", str(e))
        return False
    except Exception as e:
        logger.error("Unexpected error sending contact notification: %s", str(e))
        return False
