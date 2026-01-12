from sqlalchemy import Column, Integer, String, DateTime, func
from app.db import Base

class WaitlistEntry(Base):
    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), nullable=False, index=True)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
