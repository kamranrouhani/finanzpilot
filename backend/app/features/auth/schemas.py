"""Pydantic schemas for authentication."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username is alphanumeric or email format."""
        # Allow email addresses (contains @)
        if "@" in v:
            # Basic email validation - must have @ and . after @
            if v.count("@") != 1:
                raise ValueError("Invalid email format")
            local, domain = v.split("@")
            if not local or not domain or "." not in domain:
                raise ValueError("Invalid email format")
            return v

        # Otherwise validate as alphanumeric username
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (can include _ and -) or a valid email")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}
