"""Budget Pydantic schemas."""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BudgetBase(BaseModel):
    """Base budget schema with common fields."""

    category_id: UUID = Field(..., description="Category ID for this budget")
    amount: Decimal = Field(..., ge=0, description="Budget amount in EUR")
    period: str = Field(default="monthly", description="Budget period: monthly, weekly, yearly")
    start_date: date = Field(..., description="Budget start date")
    end_date: Optional[date] = Field(None, description="Optional budget end date")
    is_active: bool = Field(default=True, description="Whether budget is active")


class BudgetCreate(BudgetBase):
    """Schema for creating a new budget."""

    pass


class BudgetUpdate(BaseModel):
    """Schema for updating an existing budget."""

    category_id: Optional[UUID] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    period: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class BudgetResponse(BudgetBase):
    """Schema for budget response."""

    id: UUID
    user_id: UUID
    created_at: date
    updated_at: date

    model_config = ConfigDict(from_attributes=True)


class BudgetWithProgress(BudgetResponse):
    """Budget with spending progress information."""

    spent: Decimal = Field(..., description="Amount spent in current period")
    remaining: Decimal = Field(..., description="Amount remaining in budget")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of budget spent")
    is_over_budget: bool = Field(..., description="Whether budget has been exceeded")
    category_name: Optional[str] = Field(None, description="Category name")
    category_name_de: Optional[str] = Field(None, description="German category name")


class BudgetSummary(BaseModel):
    """Summary of all budgets for a user."""

    total_budgeted: Decimal = Field(..., description="Total amount budgeted")
    total_spent: Decimal = Field(..., description="Total amount spent")
    total_remaining: Decimal = Field(..., description="Total amount remaining")
    budgets: list[BudgetWithProgress] = Field(..., description="List of budgets with progress")
    over_budget_count: int = Field(..., description="Number of budgets over limit")
