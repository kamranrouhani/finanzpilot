"""Budget service logic."""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.budgets.models import Budget
from app.features.budgets.schemas import (BudgetCreate, BudgetSummary,
                                         BudgetUpdate, BudgetWithProgress)
from app.features.categories.models import Category
from app.features.transactions.models import Transaction


def _get_period_dates(budget: Budget, current_date: date = None) -> tuple[date, date]:
    """Calculate start and end dates for the current budget period.

    Args:
        budget: Budget instance
        current_date: Date to calculate period for (defaults to today)

    Returns:
        Tuple of (period_start, period_end)
    """
    if current_date is None:
        current_date = date.today()

    if budget.period == "weekly":
        # Find start of week (Monday)
        days_since_monday = current_date.weekday()
        period_start = current_date - timedelta(days=days_since_monday)
        period_end = period_start + timedelta(days=6)
    elif budget.period == "yearly":
        period_start = date(current_date.year, 1, 1)
        period_end = date(current_date.year, 12, 31)
    else:  # monthly (default)
        period_start = date(current_date.year, current_date.month, 1)
        # Calculate last day of month
        if current_date.month == 12:
            period_end = date(current_date.year, 12, 31)
        else:
            next_month = date(current_date.year, current_date.month + 1, 1)
            period_end = next_month - timedelta(days=1)

    # If budget has an end_date, don't go beyond it
    if budget.end_date and period_end > budget.end_date:
        period_end = budget.end_date

    # Don't start before budget start_date
    if period_start < budget.start_date:
        period_start = budget.start_date

    return period_start, period_end


async def calculate_budget_spent(
    db: AsyncSession,
    user_id: UUID,
    budget: Budget
) -> Decimal:
    """Calculate total amount spent for a budget in current period.

    Args:
        db: Database session
        user_id: User ID
        budget: Budget instance

    Returns:
        Decimal amount spent (negative expenses)
    """
    period_start, period_end = _get_period_dates(budget)

    # Query transactions for this category in the current period
    # Include both main category and subcategories
    query = select(func.sum(Transaction.amount)).where(
        and_(
            Transaction.user_id == user_id,
            Transaction.date >= period_start,
            Transaction.date <= period_end,
            Transaction.amount < 0,  # Only expenses (negative amounts)
            or_(
                Transaction.category_id == budget.category_id,
                Transaction.subcategory_id == budget.category_id
            )
        )
    )

    result = await db.execute(query)
    spent = result.scalar_one_or_none()

    # Return absolute value (convert negative to positive)
    return abs(spent) if spent else Decimal("0.00")


async def create_budget(
    db: AsyncSession,
    user_id: UUID,
    budget_data: BudgetCreate
) -> Budget:
    """Create a new budget.

    Args:
        db: Database session
        user_id: User ID
        budget_data: Budget creation data

    Returns:
        Created Budget instance
    """
    # Verify category exists
    category_result = await db.execute(
        select(Category).where(Category.id == budget_data.category_id)
    )
    category = category_result.scalar_one_or_none()
    if not category:
        raise ValueError(f"Category {budget_data.category_id} not found")

    # Validate period
    valid_periods = ["monthly", "weekly", "yearly"]
    if budget_data.period not in valid_periods:
        raise ValueError(f"Period must be one of: {', '.join(valid_periods)}")

    budget = Budget(
        user_id=user_id,
        **budget_data.model_dump()
    )

    db.add(budget)
    await db.commit()
    await db.refresh(budget)

    return budget


async def get_budget(
    db: AsyncSession,
    user_id: UUID,
    budget_id: UUID
) -> Optional[Budget]:
    """Get a budget by ID.

    Args:
        db: Database session
        user_id: User ID
        budget_id: Budget ID

    Returns:
        Budget instance or None
    """
    result = await db.execute(
        select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.user_id == user_id
            )
        )
    )
    return result.scalar_one_or_none()


async def list_budgets(
    db: AsyncSession,
    user_id: UUID,
    is_active: Optional[bool] = None
) -> list[Budget]:
    """List all budgets for a user.

    Args:
        db: Database session
        user_id: User ID
        is_active: Optional filter for active/inactive budgets

    Returns:
        List of Budget instances
    """
    query = select(Budget).where(Budget.user_id == user_id)

    if is_active is not None:
        query = query.where(Budget.is_active == is_active)

    query = query.order_by(Budget.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_budget(
    db: AsyncSession,
    user_id: UUID,
    budget_id: UUID,
    budget_data: BudgetUpdate
) -> Optional[Budget]:
    """Update a budget.

    Args:
        db: Database session
        user_id: User ID
        budget_id: Budget ID
        budget_data: Budget update data

    Returns:
        Updated Budget instance or None
    """
    budget = await get_budget(db, user_id, budget_id)
    if not budget:
        return None

    # Update fields
    update_dict = budget_data.model_dump(exclude_unset=True)

    # Validate period if provided
    if "period" in update_dict:
        valid_periods = ["monthly", "weekly", "yearly"]
        if update_dict["period"] not in valid_periods:
            raise ValueError(f"Period must be one of: {', '.join(valid_periods)}")

    # Validate category if provided
    if "category_id" in update_dict:
        category_result = await db.execute(
            select(Category).where(Category.id == update_dict["category_id"])
        )
        category = category_result.scalar_one_or_none()
        if not category:
            raise ValueError(f"Category {update_dict['category_id']} not found")

    for key, value in update_dict.items():
        setattr(budget, key, value)

    await db.commit()
    await db.refresh(budget)

    return budget


async def delete_budget(
    db: AsyncSession,
    user_id: UUID,
    budget_id: UUID
) -> bool:
    """Delete a budget.

    Args:
        db: Database session
        user_id: User ID
        budget_id: Budget ID

    Returns:
        True if deleted, False if not found
    """
    budget = await get_budget(db, user_id, budget_id)
    if not budget:
        return False

    await db.delete(budget)
    await db.commit()

    return True


async def get_budget_with_progress(
    db: AsyncSession,
    user_id: UUID,
    budget: Budget
) -> BudgetWithProgress:
    """Get budget with spending progress information.

    Args:
        db: Database session
        user_id: User ID
        budget: Budget instance

    Returns:
        BudgetWithProgress schema
    """
    spent = await calculate_budget_spent(db, user_id, budget)
    remaining = budget.amount - spent
    percentage = float((spent / budget.amount * 100) if budget.amount > 0 else 0)
    is_over_budget = spent > budget.amount

    # Get category name
    category_result = await db.execute(
        select(Category).where(Category.id == budget.category_id)
    )
    category = category_result.scalar_one_or_none()

    return BudgetWithProgress(
        id=budget.id,
        user_id=budget.user_id,
        category_id=budget.category_id,
        amount=budget.amount,
        period=budget.period,
        start_date=budget.start_date,
        end_date=budget.end_date,
        is_active=budget.is_active,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        spent=spent,
        remaining=remaining,
        percentage=percentage,
        is_over_budget=is_over_budget,
        category_name=category.name if category else None,
        category_name_de=category.name_de if category else None
    )


async def get_budget_summary(
    db: AsyncSession,
    user_id: UUID
) -> BudgetSummary:
    """Get summary of all budgets for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        BudgetSummary schema
    """
    budgets = await list_budgets(db, user_id, is_active=True)

    budgets_with_progress = []
    total_budgeted = Decimal("0.00")
    total_spent = Decimal("0.00")
    over_budget_count = 0

    for budget in budgets:
        budget_progress = await get_budget_with_progress(db, user_id, budget)
        budgets_with_progress.append(budget_progress)

        total_budgeted += budget.amount
        total_spent += budget_progress.spent

        if budget_progress.is_over_budget:
            over_budget_count += 1

    total_remaining = total_budgeted - total_spent

    return BudgetSummary(
        total_budgeted=total_budgeted,
        total_spent=total_spent,
        total_remaining=total_remaining,
        budgets=budgets_with_progress,
        over_budget_count=over_budget_count
    )
