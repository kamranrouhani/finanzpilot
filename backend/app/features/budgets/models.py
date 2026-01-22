"""Budget model."""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Column, Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.shared.models import TimestampMixin, UUIDMixin


class Budget(Base, UUIDMixin, TimestampMixin):
    """Budget model for tracking spending limits.

    Allows users to set spending budgets per category for different periods.
    """

    __tablename__ = "budgets"

    # User ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Category link
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)

    # Budget details
    amount = Column(Numeric(12, 2), nullable=False)  # Budget amount in EUR
    period = Column(String(10), default="monthly", nullable=False)  # "monthly", "weekly", "yearly"
    start_date = Column(Date, nullable=False)  # When budget period starts
    end_date = Column(Date, nullable=True)  # Optional end date for budget

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="budgets")
    category = relationship("Category")

    def __repr__(self) -> str:
        return f"<Budget(id={self.id}, category_id={self.category_id}, amount={self.amount}, period={self.period})>"
