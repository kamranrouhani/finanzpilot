"""Transaction API routes."""
import logging
from typing import Optional
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_db, get_current_user
from app.features.auth.models import User
from app.features.transactions.service import TransactionService
from app.features.transactions.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionImportResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/import", response_model=TransactionImportResponse)
async def import_transactions(
    file: UploadFile = File(...),
    skip_duplicates: bool = Query(True, description="Skip duplicate transactions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Import transactions from Finanzguru XLSX or CSV file.

    Supports duplicate detection based on transaction hash.
    """
    service = TransactionService(db)
    return await service.import_from_file(
        user_id=current_user.id,
        file=file,
        skip_duplicates=skip_duplicates
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new transaction manually."""
    service = TransactionService(db)
    return await service.create_transaction(current_user.id, data)


@router.get("/stats/summary", response_model=dict)
async def get_transaction_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get transaction statistics.

    Returns total income, expenses, balance, and transaction count.
    """
    service = TransactionService(db)
    return await service.get_statistics(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single transaction by ID."""
    service = TransactionService(db)
    transaction = await service.get_transaction(transaction_id, current_user.id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return transaction


@router.get("", response_model=dict)
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List transactions with filtering and pagination.

    Filters:
    - start_date: Filter transactions from this date (inclusive)
    - end_date: Filter transactions until this date (inclusive)
    - category_id: Filter by category or subcategory ID
    - search: Search in counterparty and description
    """
    service = TransactionService(db)
    transactions, total = await service.list_transactions(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        search=search,
    )

    return {
        "items": transactions,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a transaction."""
    service = TransactionService(db)
    transaction = await service.update_transaction(
        transaction_id, current_user.id, data
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a transaction."""
    service = TransactionService(db)
    deleted = await service.delete_transaction(transaction_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
