import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


def normalize_nigerian_phone(phone: str) -> str:
    """
    Normalize Nigerian phone number to +234 format.
    
    Accepts:
    - Local format: 08012345678 → +2348012345678
    - International: +2348012345678 → +2348012345678
    - With spaces/dashes: 080-1234-5678 → +2348012345678
    """
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r"[\s\-\(\)]+", "", phone)
    
    # If starts with 0, replace with +234
    if cleaned.startswith("0"):
        cleaned = "+234" + cleaned[1:]
    # If starts with 234 (no +), add +
    elif cleaned.startswith("234"):
        cleaned = "+" + cleaned
    # If doesn't start with +234, assume local and add prefix
    elif not cleaned.startswith("+234"):
        cleaned = "+234" + cleaned
    
    return cleaned


def validate_nigerian_phone(phone: str) -> str:
    """Validate and normalize Nigerian phone number."""
    normalized = normalize_nigerian_phone(phone)
    
    # Nigerian numbers: +234 followed by 10 digits
    # Valid prefixes after 234: 70, 80, 81, 90, 91, etc.
    pattern = r"^\+234[789][01]\d{8}$"
    
    if not re.match(pattern, normalized):
        raise ValueError(
            "Invalid Nigerian phone number. "
            "Expected format: 08012345678 or +2348012345678"
        )
    
    return normalized


class WaitlistIn(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(..., description="Nigerian phone number (e.g., 08012345678)")
    source: str | None = Field(default=None, max_length=100)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_and_title_case(cls, v: str) -> str:
        return v.strip().title()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_nigerian_phone(v)


class WaitlistOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    source: str | None
    created_at: datetime
