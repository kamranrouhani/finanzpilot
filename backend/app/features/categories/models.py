"""Category and TaxCategory models."""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.shared.models import TimestampMixin, UUIDMixin


class Category(Base, UUIDMixin, TimestampMixin):
    """Category model for hierarchical transaction categorization."""

    __tablename__ = "categories"

    # Basic info
    name = Column(String(50), nullable=False)
    name_de = Column(String(50), nullable=True)  # German translation

    # Hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    # Type
    is_income = Column(Boolean, default=False, nullable=False)

    # Display
    icon = Column(String(50), nullable=True)  # Lucide icon name
    color = Column(String(7), nullable=True)  # Hex color code
    sort_order = Column(Integer, default=0, nullable=False)

    # Relationships
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Category", back_populates="children", remote_side="Category.id")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name}, parent_id={self.parent_id})>"


class TaxCategory(Base, UUIDMixin, TimestampMixin):
    """Tax category model for German tax-deductible expenses (Steuerkategorien)."""

    __tablename__ = "tax_categories"

    # Basic info
    name = Column(String(50), unique=True, nullable=False, index=True)
    name_de = Column(String(100), nullable=False)  # German name (official)

    # Tax form info
    anlage = Column(String(50), nullable=True)  # Which tax form (Anlage N, Sonderausgaben, etc.)
    description = Column(String(500), nullable=True)

    # Deductibility
    deductible_percent = Column(Integer, default=100, nullable=False)  # Percentage deductible

    def __repr__(self) -> str:
        return f"<TaxCategory(id={self.id}, name={self.name}, anlage={self.anlage})>"
