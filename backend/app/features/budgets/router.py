"""Budget API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User
from app.features.budgets import service
from app.features.budgets.schemas import (BudgetCreate, BudgetResponse,
                                         BudgetSummary, BudgetUpdate,
                                         BudgetWithProgress)
from app.shared.dependencies import get_current_user, get_db

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new budget.

    Args:
        budget_data: Budget creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created budget

    Raises:
        HTTPException: If category not found or invalid data
    """
    try:
        budget = await service.create_budget(db, current_user.id, budget_data)
        return budget
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=list[BudgetResponse])
async def list_budgets(
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all budgets for the authenticated user.

    Args:
        is_active: Optional filter for active/inactive budgets
        db: Database session
        current_user: Authenticated user

    Returns:
        List of budgets
    """
    budgets = await service.list_budgets(db, current_user.id, is_active)
    return budgets


@router.get("/summary", response_model=BudgetSummary)
async def get_budget_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary of all budgets with spending progress.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        Budget summary with progress information
    """
    summary = await service.get_budget_summary(db, current_user.id)
    return summary


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific budget by ID.

    Args:
        budget_id: Budget ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Budget instance

    Raises:
        HTTPException: If budget not found
    """
    budget = await service.get_budget(db, current_user.id, budget_id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget {budget_id} not found"
        )
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    budget_data: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a budget.

    Args:
        budget_id: Budget ID
        budget_data: Budget update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated budget

    Raises:
        HTTPException: If budget not found or invalid data
    """
    try:
        budget = await service.update_budget(db, current_user.id, budget_id, budget_data)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Budget {budget_id} not found"
            )
        return budget
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a budget.

    Args:
        budget_id: Budget ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If budget not found
    """
    deleted = await service.delete_budget(db, current_user.id, budget_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget {budget_id} not found"
        )
