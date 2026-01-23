from sqlalchemy import Column, Integer, String, DateTime, func
from app.db import Base


class WaitlistEntry(Base):
    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(320), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
