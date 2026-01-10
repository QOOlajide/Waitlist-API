from pydantic import BaseModel, EmailStr, Field

class WaitlistIn(BaseModel):
    email: EmailStr
    source: str | None = Field(default=None, max_length=100)

class WaitlistOut(BaseModel):
    id: int
    email: EmailStr
    source: str | None
    created_at: str
