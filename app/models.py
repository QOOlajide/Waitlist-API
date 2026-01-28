import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


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


# =============================================================================
# Contact Us Models
# =============================================================================

# Common spam phrases to detect
SPAM_PATTERNS = [
    r"\b(viagra|cialis|casino|lottery|winner|prize|click here|act now)\b",
    r"\b(earn money|make money fast|work from home|mlm)\b",
    r"\b(crypto|bitcoin|investment opportunity|guaranteed returns)\b",
    r"(https?://\S+){3,}",  # 3+ URLs is suspicious
    r"(.)\1{10,}",  # 10+ repeated characters
]

# Compile patterns for performance
SPAM_REGEX = [re.compile(p, re.IGNORECASE) for p in SPAM_PATTERNS]


def detect_spam_signals(text: str) -> list[str]:
    """
    Detect spam signals in text. Returns list of triggered patterns.
    """
    signals = []
    for pattern in SPAM_REGEX:
        if pattern.search(text):
            signals.append(pattern.pattern)
    return signals


def contains_excessive_links(text: str) -> bool:
    """Check if text contains excessive URLs (common spam indicator)."""
    url_pattern = r"https?://\S+"
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    return len(urls) > 2


def is_gibberish(text: str) -> bool:
    """
    Basic gibberish detection:
    - Very low ratio of vowels to consonants
    - Excessive special characters
    """
    if len(text) < 10:
        return False
    
    # Count vowels vs consonants
    vowels = len(re.findall(r"[aeiouAEIOU]", text))
    consonants = len(re.findall(r"[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]", text))
    
    if consonants > 0 and vowels / consonants < 0.1:
        return True
    
    # Excessive special characters
    special = len(re.findall(r"[^a-zA-Z0-9\s.,!?'-]", text))
    if special > len(text) * 0.3:
        return True
    
    return False


class ContactMessageIn(BaseModel):
    """
    Contact form input with strong validation and spam detection.
    
    Frontend must NOT render the honeypot field (website) visually.
    Bots will fill it, humans won't.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Your full name",
        examples=["John Doe"]
    )
    email: EmailStr = Field(
        ...,
        description="Your email address",
        examples=["john@example.com"]
    )
    subject: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Message subject",
        examples=["Question about your service"]
    )
    message: str = Field(
        ...,
        min_length=20,
        max_length=5000,
        description="Your message (20-5000 characters)",
        examples=["I'd like to learn more about your services..."]
    )
    
    # Honeypot field - should be empty. Bots auto-fill this.
    # Frontend: render as hidden field or use CSS to hide it
    website: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Leave this field empty (anti-spam)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        # Name should contain at least one letter
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Name must contain at least one letter")
        # Block names that are just numbers or special chars
        if re.match(r"^[\d\W]+$", v):
            raise ValueError("Invalid name format")
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        v = v.strip()
        # Subject should not be all caps (spam indicator)
        if len(v) > 10 and v == v.upper():
            raise ValueError("Please don't use all caps in subject")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        
        # Check for gibberish
        if is_gibberish(v):
            raise ValueError("Message appears to be invalid")
        
        # Check for excessive links
        if contains_excessive_links(v):
            raise ValueError("Message contains too many links")
        
        return v

    @model_validator(mode="after")
    def check_honeypot_and_spam(self) -> "ContactMessageIn":
        # Honeypot check: if 'website' has any value, it's a bot
        if self.website:
            raise ValueError("Spam detected")
        
        # Check combined text for spam patterns
        combined_text = f"{self.name} {self.subject} {self.message}"
        spam_signals = detect_spam_signals(combined_text)
        
        if len(spam_signals) >= 2:
            raise ValueError("Message flagged as potential spam")
        
        return self


class ContactMessageOut(BaseModel):
    """Response after successfully submitting a contact message."""
    id: int
    name: str
    email: EmailStr
    subject: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class ContactMessageResponse(BaseModel):
    """
    User-friendly response for contact form submission.
    Doesn't expose internal IDs for security.
    """
    success: bool = True
    message: str = "Thank you! We've received your message and will respond soon."
