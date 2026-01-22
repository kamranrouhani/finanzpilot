"""AI feature API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai import service
from app.features.ai.schemas import (BulkCategorizationRequest,
                                    BulkCategorizationResponse,
                                    CategorySuggestion,
                                    CategorySuggestionRequest)
from app.features.auth.models import User
from app.shared.dependencies import get_current_user, get_db

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/categorize", response_model=CategorySuggestion)
async def suggest_category(
    request: CategorySuggestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Suggest a category for a transaction using AI.

    Args:
        request: Transaction details
        db: Database session
        current_user: Authenticated user

    Returns:
        CategorySuggestion with category and confidence score

    Raises:
        HTTPException: If AI service fails
    """
    try:
        suggestion = await service.suggest_category_for_transaction(
            db,
            request.counterparty,
            request.description,
            request.amount
        )
        return suggestion
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI categorization failed: {str(e)}"
        )


@router.post("/categorize/bulk", response_model=BulkCategorizationResponse)
async def bulk_categorize(
    request: BulkCategorizationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Categorize multiple transactions in bulk using AI.

    Args:
        request: List of transaction IDs
        db: Database session
        current_user: Authenticated user

    Returns:
        BulkCategorizationResponse with results for each transaction

    Raises:
        HTTPException: If request is invalid
    """
    if not request.transaction_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transaction IDs provided"
        )

    result = await service.bulk_categorize_transactions(
        db,
        current_user.id,
        request.transaction_ids
    )

    return BulkCategorizationResponse(**result)
