import csv
import io
import os
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db, get_engine
from app.email import send_contact_notification, send_welcome_email
from app.models import ContactMessageIn, ContactMessageResponse, WaitlistIn, WaitlistOut
from app.models_db import ContactMessage, WaitlistEntry
from app.service import RateLimitExceeded, add_to_waitlist, save_contact_message

router = APIRouter()

# Admin API key for protected endpoints
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")


def verify_admin_key(key: str = Query(..., description="Admin API key")):
    """Verify the admin API key from query parameter."""
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY not configured")
    if key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@router.get("/")
def root():
    return {
        "name": "Waitlist API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }

@router.get("/health")
def health():
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

@router.post("/waitlist", response_model=WaitlistOut, status_code=201)
def join_waitlist(
    payload: WaitlistIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    result = add_to_waitlist(db, payload)

    # Queue personalized welcome email (non-blocking)
    background_tasks.add_task(send_welcome_email, result["email"], result["first_name"])

    return result


@router.get("/admin/export")
def export_waitlist_csv(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    """
    Export all waitlist entries as CSV.
    
    Requires admin API key: ?key=YOUR_ADMIN_KEY
    """
    # Query all entries ordered by signup date
    entries = db.query(WaitlistEntry).order_by(WaitlistEntry.created_at.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow(["id", "first_name", "last_name", "email", "phone", "source", "created_at"])
    
    # Data rows
    for entry in entries:
        writer.writerow([
            entry.id,
            entry.first_name,
            entry.last_name,
            entry.email,
            entry.phone,
            entry.source or "",
            entry.created_at.isoformat() if entry.created_at else "",
        ])
    
    # Prepare response
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"waitlist_export_{timestamp}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# =============================================================================
# Contact Form Endpoints
# =============================================================================

def get_client_ip(request: Request) -> str | None:
    """
    Extract client IP from request, handling proxies (Vercel, Cloudflare, etc.).
    
    Order of precedence:
    1. CF-Connecting-IP (Cloudflare)
    2. X-Forwarded-For (standard proxy header)
    3. X-Real-IP (nginx)
    4. Direct client host
    """
    # Cloudflare
    if cf_ip := request.headers.get("CF-Connecting-IP"):
        return cf_ip.strip()
    
    # X-Forwarded-For (may contain multiple IPs: client, proxy1, proxy2)
    if xff := request.headers.get("X-Forwarded-For"):
        # First IP is the original client
        return xff.split(",")[0].strip()
    
    # X-Real-IP
    if real_ip := request.headers.get("X-Real-IP"):
        return real_ip.strip()
    
    # Direct connection
    if request.client:
        return request.client.host
    
    return None


@router.post(
    "/contact",
    response_model=ContactMessageResponse,
    status_code=201,
    summary="Submit contact form",
    description="""
    Submit a contact form message.
    
    **Validation:**
    - Name: 2-100 characters, must contain letters
    - Email: Valid email format
    - Subject: 5-200 characters
    - Message: 20-5000 characters
    
    **Anti-Spam:**
    - Honeypot field detection
    - Spam phrase detection
    - Rate limiting per IP (5/hour) and email (3/hour)
    - Gibberish detection
    
    **Note for Frontend:**
    Include the `website` field in your form but hide it with CSS.
    Bots will fill it, humans won't. If filled, submission is rejected.
    """,
    responses={
        201: {"description": "Message submitted successfully"},
        400: {"description": "Validation error (spam detected, invalid input)"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Server error"},
    },
)
def submit_contact(
    payload: ContactMessageIn,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ContactMessageResponse:
    """
    Handle contact form submissions.
    
    Validates input, checks rate limits, saves to database,
    and sends notification email in background.
    """
    # Get client info for rate limiting and logging
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    try:
        # Save to database (includes rate limit check)
        message = save_contact_message(
            db=db,
            payload=payload,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        
        # Queue notification email (non-blocking)
        background_tasks.add_task(
            send_contact_notification,
            sender_name=message.name,
            sender_email=message.email,
            subject=message.subject,
            message=message.message,
            ip_address=client_ip,
        )
        
        return ContactMessageResponse(
            success=True,
            message="Thank you! We've received your message and will respond soon.",
        )
        
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/admin/contacts")
def list_contact_messages(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key),
    unread_only: bool = Query(False, description="Only show unread messages"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
):
    """
    List contact form submissions (admin only).
    
    Requires admin API key: ?key=YOUR_ADMIN_KEY
    """
    query = db.query(ContactMessage).order_by(ContactMessage.created_at.desc())
    
    if unread_only:
        query = query.filter(ContactMessage.is_read == False)  # noqa: E712
    
    messages = query.limit(limit).all()
    
    return {
        "count": len(messages),
        "messages": [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "subject": m.subject,
                "message": m.message,
                "ip_address": m.ip_address,
                "is_spam": m.is_spam,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.patch("/admin/contacts/{message_id}")
def update_contact_message(
    message_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key),
    is_read: bool | None = Query(None, description="Mark as read/unread"),
    is_spam: bool | None = Query(None, description="Mark as spam/not spam"),
):
    """
    Update a contact message status (admin only).
    
    Requires admin API key: ?key=YOUR_ADMIN_KEY
    """
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if is_read is not None:
        message.is_read = is_read
    if is_spam is not None:
        message.is_spam = is_spam
    
    db.commit()
    db.refresh(message)
    
    return {
        "id": message.id,
        "is_read": message.is_read,
        "is_spam": message.is_spam,
        "updated": True,
    }
