"""Transaction service with business logic."""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from decimal import Decimal, InvalidOperation
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status

from app.features.transactions.models import Transaction
from app.features.transactions.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionImportResponse,
)
from app.features.transactions.finanzguru_parser import parse_finanzguru_file
from app.features.categories.models import Category
from tempfile import NamedTemporaryFile
import os

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for transaction operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_transaction(
        self, user_id: UUID, data: TransactionCreate
    ) -> Transaction:
        """Create a new transaction manually."""
        transaction = Transaction(
            user_id=user_id,
            **data.model_dump(exclude_unset=True)
        )
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def get_transaction(
        self, transaction_id: UUID, user_id: UUID
    ) -> Optional[Transaction]:
        """Get a single transaction by ID."""
        result = await self.db.execute(
            select(Transaction).where(
                and_(
                    Transaction.id == transaction_id,
                    Transaction.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_transactions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[UUID] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Transaction], int]:
        """List transactions with filtering and pagination."""
        # Build query
        query = select(Transaction).where(Transaction.user_id == user_id)

        # Apply filters
        if start_date:
            query = query.where(Transaction.date >= start_date)
        if end_date:
            query = query.where(Transaction.date <= end_date)
        if category_id:
            query = query.where(
                or_(
                    Transaction.category_id == category_id,
                    Transaction.subcategory_id == category_id
                )
            )
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Transaction.counterparty.ilike(search_pattern),
                    Transaction.description.ilike(search_pattern)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar()

        # Apply pagination and ordering
        query = query.order_by(Transaction.date.desc())
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        transactions = result.scalars().all()

        return transactions, total_count

    async def update_transaction(
        self, transaction_id: UUID, user_id: UUID, data: TransactionUpdate
    ) -> Optional[Transaction]:
        """Update a transaction."""
        transaction = await self.get_transaction(transaction_id, user_id)
        if not transaction:
            return None

        # Update fields
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(transaction, field, value)

        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def delete_transaction(
        self, transaction_id: UUID, user_id: UUID
    ) -> bool:
        """Delete a transaction."""
        transaction = await self.get_transaction(transaction_id, user_id)
        if not transaction:
            return False

        await self.db.delete(transaction)
        await self.db.commit()
        return True

    async def import_from_file(
        self, user_id: UUID, file: UploadFile, skip_duplicates: bool = True
    ) -> TransactionImportResponse:
        """
        Import transactions from Finanzguru XLSX/CSV file.

        Args:
            user_id: User ID
            file: Uploaded file
            skip_duplicates: Whether to skip duplicate transactions

        Returns:
            Import statistics
        """
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )

        allowed_extensions = [".xlsx", ".csv"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {allowed_extensions}"
            )

        # Save uploaded file temporarily
        temp_path = None
        try:
            with NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_path = temp_file.name
                content = await file.read()
                temp_file.write(content)
                temp_file.flush()
            # Parse file
            parsed_transactions = parse_finanzguru_file(temp_path)

            # Import statistics
            stats = {
                "total_rows": len(parsed_transactions),
                "imported": 0,
                "skipped": 0,
                "errors": 0,
                "error_details": [],
            }

            # Check for existing transactions by hash
            if skip_duplicates and parsed_transactions:
                import_hashes = [t["import_hash"] for t in parsed_transactions]
                result = await self.db.execute(
                    select(Transaction.import_hash).where(
                        and_(
                            Transaction.user_id == user_id,
                            Transaction.import_hash.in_(import_hashes)
                        )
                    )
                )
                existing_hashes = set(result.scalars().all())
            else:
                existing_hashes = set()

            # Process each transaction
            for tx_data in parsed_transactions:
                try:
                    # Skip duplicates (check both DB and current batch)
                    if skip_duplicates and tx_data["import_hash"] in existing_hashes:
                        stats["skipped"] += 1
                        continue

                    # Extract account info
                    account_iban_last4 = None
                    if tx_data.get("account_iban"):
                        account_iban = tx_data["account_iban"]
                        account_iban_last4 = account_iban[-4:] if len(account_iban) >= 4 else None

                    # Map Finanzguru categories to our categories (best effort)
                    category_id, subcategory_id = await self._map_categories(
                        tx_data.get("category"),
                        tx_data.get("subcategory")
                    )

                    # Parse tags - split comma-separated string into array
                    tags = None
                    if tx_data.get("tags"):
                        tags = [tag.strip() for tag in tx_data["tags"].split(",") if tag.strip()]

                    # Parse balance_after from balance field
                    balance_after = None
                    if tx_data.get("balance"):
                        try:
                            balance_after = Decimal(str(tx_data["balance"]))
                        except (InvalidOperation, ValueError):
                            pass

                    # Parse fg_analysis_amount from analysis_amount field
                    fg_analysis_amount = None
                    if tx_data.get("analysis_amount"):
                        try:
                            fg_analysis_amount = Decimal(str(tx_data["analysis_amount"]))
                        except (InvalidOperation, ValueError):
                            pass

                    # Create transaction
                    transaction = Transaction(
                        user_id=user_id,
                        account_name=tx_data.get("account_name"),
                        account_iban_last4=account_iban_last4,
                        date=tx_data["date"],
                        amount=tx_data["amount"],
                        currency=tx_data.get("currency", "EUR"),
                        balance_after=balance_after,
                        counterparty=tx_data.get("counterparty"),
                        counterparty_iban=tx_data.get("counterparty_iban"),
                        description=tx_data.get("description"),
                        e_ref=tx_data.get("e_ref"),
                        mandate_ref=tx_data.get("mandate_ref"),
                        creditor_id=tx_data.get("creditor_id"),
                        category_id=category_id,
                        subcategory_id=subcategory_id,
                        # Finanzguru metadata
                        fg_main_category=tx_data.get("category"),
                        fg_subcategory=tx_data.get("subcategory"),
                        fg_contract_name=tx_data.get("fg_contract"),
                        fg_contract_frequency=tx_data.get("fg_contract_frequency"),
                        fg_contract_id=tx_data.get("fg_contract_id"),
                        fg_is_transfer=tx_data.get("fg_is_transfer", False),
                        fg_excluded_from_budget=tx_data.get("fg_excluded_from_budget", False),
                        fg_transaction_type=tx_data.get("fg_transaction_type"),
                        fg_analysis_amount=fg_analysis_amount,
                        fg_week=tx_data.get("fg_week"),
                        fg_month=tx_data.get("fg_month"),
                        fg_quarter=tx_data.get("fg_quarter"),
                        fg_year=tx_data.get("fg_year"),
                        tags=tags,
                        notes=tx_data.get("notes"),
                        source="finanzguru",
                        import_hash=tx_data["import_hash"],
                    )

                    self.db.add(transaction)
                    stats["imported"] += 1

                    # Add hash to existing_hashes to prevent duplicates within this batch
                    if tx_data["import_hash"]:
                        existing_hashes.add(tx_data["import_hash"])

                except Exception as e:
                    stats["errors"] += 1
                    stats["error_details"].append(str(e))
                    logger.error(f"Error importing transaction: {e}")

            # Commit all transactions
            await self.db.commit()

            return TransactionImportResponse(**stats)

        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    async def _map_categories(
        self, fg_category: Optional[str], fg_subcategory: Optional[str]
    ) -> tuple[Optional[UUID], Optional[UUID]]:
        """
        Map Finanzguru category names to our category IDs.

        Returns:
            Tuple of (category_id, subcategory_id)
        """
        category_id = None
        subcategory_id = None

        if not fg_category:
            return None, None

        # Try to find matching category by name_de (German name)
        result = await self.db.execute(
            select(Category).where(
                and_(
                    Category.name_de == fg_category,
                    Category.parent_id.is_(None)  # Top-level category
                )
            )
        )
        category = result.scalar_one_or_none()

        if category:
            category_id = category.id

            # Try to find subcategory
            if fg_subcategory:
                result = await self.db.execute(
                    select(Category).where(
                        and_(
                            Category.name_de == fg_subcategory,
                            Category.parent_id == category_id
                        )
                    )
                )
                subcategory = result.scalar_one_or_none()
                if subcategory:
                    subcategory_id = subcategory.id

        return category_id, subcategory_id

    async def get_statistics(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get transaction statistics using database aggregation."""
        # Use database-level aggregation for better performance
        query = select(
            func.sum(func.case((Transaction.amount > 0, Transaction.amount), else_=0)).label("total_income"),
            func.sum(func.case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label("total_expenses"),
            func.count(Transaction.id).label("transaction_count")
        ).where(Transaction.user_id == user_id)

        if start_date:
            query = query.where(Transaction.date >= start_date)
        if end_date:
            query = query.where(Transaction.date <= end_date)

        result = await self.db.execute(query)
        row = result.first()

        # Extract aggregated values (handle None values from empty results)
        total_income = row.total_income or 0
        total_expenses = row.total_expenses or 0
        balance = total_income - total_expenses
        count = row.transaction_count or 0

        return {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "balance": float(balance),
            "transaction_count": count,
        }
