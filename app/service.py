import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import ContactMessageIn, WaitlistIn
from app.models_db import ContactMessage, WaitlistEntry


def _is_unique_violation(err: IntegrityError) -> bool:
    # Postgres unique violation is SQLSTATE 23505 across psycopg2/psycopg3.
    orig = getattr(err, "orig", None)
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    return sqlstate == "23505"


def _get_duplicate_field(err: IntegrityError) -> str:
    """Try to determine which field caused the unique violation."""
    error_msg = str(err.orig).lower() if err.orig else ""
    if "email" in error_msg:
        return "Email"
    elif "phone" in error_msg:
        return "Phone number"
    return "Email or phone number"


def add_to_waitlist(db: Session, payload: WaitlistIn):
    email = str(payload.email).strip().lower()

    entry = WaitlistEntry(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=email,
        phone=payload.phone,  # Already normalized by validator
        source=payload.source,
    )
    db.add(entry)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if _is_unique_violation(e):
            field = _get_duplicate_field(e)
            raise HTTPException(status_code=409, detail=f"{field} already on waitlist")
        raise HTTPException(status_code=500, detail="Database integrity error")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(entry)

    return {
        "id": entry.id,
        "first_name": entry.first_name,
        "last_name": entry.last_name,
        "email": entry.email,
        "phone": entry.phone,
        "source": entry.source,
        "created_at": entry.created_at,
    }


# =============================================================================
# Contact Form Service
# =============================================================================

# Rate limit configuration (from env or defaults)
# Max submissions per IP in the time window
CONTACT_RATE_LIMIT_IP = int(os.getenv("CONTACT_RATE_LIMIT_IP", "5"))
# Max submissions per email in the time window
CONTACT_RATE_LIMIT_EMAIL = int(os.getenv("CONTACT_RATE_LIMIT_EMAIL", "3"))
# Time window in minutes
CONTACT_RATE_WINDOW_MINUTES = int(os.getenv("CONTACT_RATE_WINDOW_MINUTES", "60"))


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


def check_contact_rate_limit(
    db: Session,
    ip_address: str | None,
    email: str,
) -> None:
    """
    Check if the IP or email has exceeded rate limits.
    
    This uses the database as the source of truth for rate limiting,
    which works reliably across serverless instances.
    
    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    window_start = datetime.now(timezone.utc) - timedelta(minutes=CONTACT_RATE_WINDOW_MINUTES)
    
    # Check IP rate limit (if IP is provided)
    if ip_address:
        ip_count = db.query(func.count(ContactMessage.id)).filter(
            ContactMessage.ip_address == ip_address,
            ContactMessage.created_at >= window_start,
        ).scalar()
        
        if ip_count >= CONTACT_RATE_LIMIT_IP:
            raise RateLimitExceeded(
                f"Too many requests from this IP. Please try again later."
            )
    
    # Check email rate limit
    email_lower = email.strip().lower()
    email_count = db.query(func.count(ContactMessage.id)).filter(
        func.lower(ContactMessage.email) == email_lower,
        ContactMessage.created_at >= window_start,
    ).scalar()
    
    if email_count >= CONTACT_RATE_LIMIT_EMAIL:
        raise RateLimitExceeded(
            f"Too many requests from this email. Please try again later."
        )


def save_contact_message(
    db: Session,
    payload: ContactMessageIn,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContactMessage:
    """
    Save a contact form submission to the database.
    
    Args:
        db: Database session
        payload: Validated contact form data
        ip_address: Client IP address (for rate limiting)
        user_agent: Client user agent (for spam analysis)
    
    Returns:
        The saved ContactMessage instance
    
    Raises:
        RateLimitExceeded: If rate limit is exceeded
        HTTPException: For database errors
    """
    # Check rate limits first
    check_contact_rate_limit(db, ip_address, str(payload.email))
    
    # Normalize email
    email = str(payload.email).strip().lower()
    
    # Create the message entry
    message = ContactMessage(
        name=payload.name.strip(),
        email=email,
        subject=payload.subject.strip(),
        message=payload.message.strip(),
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,  # Truncate long user agents
        is_spam=False,
        is_read=False,
    )
    
    db.add(message)
    
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save message")
    
    db.refresh(message)
    return message
