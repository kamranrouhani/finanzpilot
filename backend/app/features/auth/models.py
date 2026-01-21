"""User model for authentication."""
from sqlalchemy import Column, String

from app.database import Base
from app.shared.models import TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
