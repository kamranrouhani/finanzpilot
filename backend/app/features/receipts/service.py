"""Receipt service for file handling and OCR."""
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.features.receipts.models import Receipt
from app.features.transactions.models import Transaction


async def cleanup_receipt_file(file_path: str) -> None:
    """
    Clean up a receipt file from disk asynchronously.

    Args:
        file_path: Path to the file to delete
    """
    try:
        # Check if file exists and remove in thread pool
        exists_and_removed = await asyncio.to_thread(_safe_remove_file, file_path)
        if exists_and_removed:
            print(f"Cleaned up orphaned receipt file: {file_path}")
    except Exception as e:
        print(f"Failed to cleanup receipt file {file_path}: {e}")
        # Don't raise - cleanup failure shouldn't break the flow


def _safe_remove_file(file_path: str) -> bool:
    """Helper function to safely remove a file (runs in thread pool)."""
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


async def save_receipt_file(
    file: BinaryIO, filename: str, user_id: str
) -> tuple[str, int]:
    """
    Save uploaded receipt file to disk asynchronously.

    Args:
        file: File object
        filename: Original filename
        user_id: User ID

    Returns:
        tuple: (stored_path, file_size)
    """
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR) / str(user_id)
    await asyncio.to_thread(upload_dir.mkdir, parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = Path(filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename

    # Read file content in thread pool
    content = await asyncio.to_thread(file.read)
    file_size = len(content)

    # Write file in thread pool
    await asyncio.to_thread(_write_file, file_path, content)

    return str(file_path), file_size


def _write_file(file_path: Path, content: bytes) -> None:
    """Helper function to write file content (runs in thread pool)."""
    with open(file_path, "wb") as f:
        f.write(content)


async def create_receipt(
    db: AsyncSession,
    user_id: str,
    filename: str,
    stored_path: str,
    file_size: int,
    mime_type: str,
) -> Receipt:
    """
    Create a new receipt record.

    Args:
        db: Database session
        user_id: User ID
        filename: Original filename
        stored_path: Path where file is stored
        file_size: Size of file in bytes
        mime_type: MIME type of file

    Returns:
        Receipt: Created receipt
    """
    receipt = Receipt(
        user_id=user_id,
        original_filename=filename,
        stored_path=stored_path,
        file_size=file_size,
        mime_type=mime_type,
        status="pending",
    )

    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)

    return receipt


async def get_user_receipts(
    db: AsyncSession, user_id: str, limit: int = 50
) -> list[Receipt]:
    """
    Get all receipts for a user.

    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of receipts to return

    Returns:
        list[Receipt]: List of receipts
    """
    result = await db.execute(
        select(Receipt)
        .where(Receipt.user_id == user_id)
        .order_by(Receipt.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def process_receipt_ocr(db: AsyncSession, receipt: Receipt) -> Receipt:
    """
    Process receipt with Ollama OCR (placeholder for Phase 1).

    Args:
        db: Database session
        receipt: Receipt to process

    Returns:
        Receipt: Updated receipt with OCR results
    """
    # Update status
    receipt.status = "processing"
    await db.commit()

    try:
        # Placeholder OCR result (Phase 1 - simplified)
        receipt.ocr_raw_text = "OCR placeholder - Ollama integration in progress"
        receipt.extracted_data = {
            "merchant": "Sample Store",
            "date": "2026-01-21",
            "total": 42.99,
            "items": [{"name": "Sample Item", "price": 42.99}],
        }
        receipt.ocr_model = "qwen2.5-vl:7b"
        receipt.ocr_processed_at = datetime.now(timezone.utc)
        receipt.status = "completed"

        await db.commit()
        await db.refresh(receipt)
    except Exception as e:
        receipt.status = "failed"
        receipt.error_message = str(e)
        await db.commit()
        await db.refresh(receipt)

    return receipt


async def find_matching_transactions(
    db: AsyncSession,
    receipt: Receipt,
    user_id: str,
    max_results: int = 10
) -> list[tuple[Transaction, float]]:
    """
    Find transactions that potentially match a receipt.

    Matches are based on:
    - Date proximity (within 7 days)
    - Amount similarity (if available in extracted_data)
    - Merchant name matching (if available)

    Args:
        db: Database session
        receipt: Receipt to match
        user_id: User ID
        max_results: Maximum number of results to return

    Returns:
        List of tuples (Transaction, confidence_score) sorted by confidence
    """
    # Extract data from receipt
    extracted_data = receipt.extracted_data or {}
    receipt_date = extracted_data.get('date') if isinstance(extracted_data.get('date'), str) else None
    receipt_total = extracted_data.get('total')
    merchant = extracted_data.get('merchant', '').lower()

    # Build base query
    query = select(Transaction).where(Transaction.user_id == user_id)

    # If we have a date, narrow down to +/- 7 days
    if receipt_date:
        try:
            date_obj = datetime.strptime(receipt_date, '%Y-%m-%d').date()
            start_date = date_obj - timedelta(days=7)
            end_date = date_obj + timedelta(days=7)
            query = query.where(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            )
        except (ValueError, TypeError):
            pass  # Invalid date, skip date filtering

    # Execute query
    result = await db.execute(query.limit(100))  # Limit to prevent huge result sets
    transactions = list(result.scalars().all())

    # Calculate confidence scores
    matches = []
    for txn in transactions:
        score = 0.0

        # Date matching (40 points max)
        if receipt_date:
            try:
                date_obj = datetime.strptime(receipt_date, '%Y-%m-%d').date()
                days_diff = abs((txn.date - date_obj).days)
                if days_diff == 0:
                    score += 40.0
                elif days_diff <= 2:
                    score += 30.0
                elif days_diff <= 7:
                    score += 20.0
            except (ValueError, TypeError):
                pass

        # Amount matching (40 points max)
        if receipt_total and txn.amount:
            try:
                receipt_amount = abs(Decimal(str(receipt_total)))
                txn_amount = abs(txn.amount)
                amount_diff = abs(receipt_amount - txn_amount)

                if amount_diff == 0:
                    score += 40.0
                elif amount_diff <= Decimal('0.01'):  # Within 1 cent
                    score += 35.0
                elif amount_diff <= Decimal('1.00'):  # Within 1 euro
                    score += 25.0
                elif amount_diff <= Decimal('5.00'):  # Within 5 euros
                    score += 15.0
            except (ValueError, TypeError, AttributeError):
                pass

        # Merchant matching (20 points max)
        if merchant and txn.counterparty:
            counterparty_lower = txn.counterparty.lower()
            if merchant in counterparty_lower or counterparty_lower in merchant:
                score += 20.0
            elif any(word in counterparty_lower for word in merchant.split() if len(word) > 3):
                score += 10.0

        # Only include transactions with some confidence
        if score >= 10.0:
            matches.append((txn, score))

    # Sort by confidence score (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)

    return matches[:max_results]


async def link_receipt_to_transaction(
    db: AsyncSession,
    receipt_id: str,
    transaction_id: str,
    user_id: str
) -> Optional[Receipt]:
    """
    Link a receipt to a transaction.

    Args:
        db: Database session
        receipt_id: Receipt ID
        transaction_id: Transaction ID
        user_id: User ID (for security check)

    Returns:
        Updated Receipt or None if not found/unauthorized
    """
    # Get receipt and verify ownership
    receipt_result = await db.execute(
        select(Receipt).where(
            and_(
                Receipt.id == receipt_id,
                Receipt.user_id == user_id
            )
        )
    )
    receipt = receipt_result.scalar_one_or_none()
    if not receipt:
        return None

    # Verify transaction exists and belongs to user
    txn_result = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            )
        )
    )
    transaction = txn_result.scalar_one_or_none()
    if not transaction:
        return None

    # Link receipt to transaction
    receipt.transaction_id = transaction_id
    await db.commit()
    await db.refresh(receipt)

    return receipt


async def unlink_receipt_from_transaction(
    db: AsyncSession,
    receipt_id: str,
    user_id: str
) -> Optional[Receipt]:
    """
    Unlink a receipt from its transaction.

    Args:
        db: Database session
        receipt_id: Receipt ID
        user_id: User ID (for security check)

    Returns:
        Updated Receipt or None if not found/unauthorized
    """
    # Get receipt and verify ownership
    receipt_result = await db.execute(
        select(Receipt).where(
            and_(
                Receipt.id == receipt_id,
                Receipt.user_id == user_id
            )
        )
    )
    receipt = receipt_result.scalar_one_or_none()
    if not receipt:
        return None

    # Unlink
    receipt.transaction_id = None
    await db.commit()
    await db.refresh(receipt)

    return receipt
