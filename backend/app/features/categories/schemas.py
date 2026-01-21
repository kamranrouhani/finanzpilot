"""Pydantic schemas for categories."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base schema for category."""

    name: str = Field(..., min_length=1, max_length=50)
    name_de: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[UUID] = None
    is_income: bool = False
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    name_de: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[UUID] = None
    is_income: Optional[bool] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryTreeResponse(CategoryResponse):
    """Schema for category with children."""

    children: List["CategoryTreeResponse"] = []

    model_config = {
        "from_attributes": True,
        # Don't try to validate lazy-loaded relationships
        "validate_assignment": False,
    }


class TaxCategoryBase(BaseModel):
    """Base schema for tax category."""

    name: str = Field(..., min_length=1, max_length=50)
    name_de: str = Field(..., min_length=1, max_length=100)
    anlage: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    deductible_percent: int = Field(100, ge=0, le=100)


class TaxCategoryCreate(TaxCategoryBase):
    """Schema for creating a tax category."""

    pass


class TaxCategoryResponse(TaxCategoryBase):
    """Schema for tax category response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
