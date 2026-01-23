from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.models_db import WaitlistEntry
from app.models import WaitlistIn


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
