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


def add_to_waitlist(db: Session, payload: WaitlistIn):
    email = str(payload.email).strip().lower()

    entry = WaitlistEntry(email=email, source=payload.source)
    db.add(entry)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if _is_unique_violation(e):
            raise HTTPException(status_code=409, detail="Email already on waitlist")
        raise HTTPException(status_code=500, detail="Database integrity error")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(entry)

    return {
        "id": entry.id,
        "email": entry.email,
        "source": entry.source,
        "created_at": entry.created_at,
    }
