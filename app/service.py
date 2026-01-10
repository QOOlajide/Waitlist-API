from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.db import SessionLocal
from app.models_db import WaitlistEntry
from app.models import WaitlistIn

def add_to_waitlist(payload: WaitlistIn):
    db = SessionLocal()
    try:
        entry = WaitlistEntry(
            email=str(payload.email).lower(),
            source=payload.source
        )
        db.add(entry)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Email already on waitlist")

        db.refresh(entry)

        return {
            "id": entry.id,
            "email": entry.email,
            "source": entry.source,
            "created_at": entry.created_at.isoformat(),
        }
    finally:
        db.close()
