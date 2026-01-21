"""Receipt service for file handling and OCR."""
import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.features.receipts.models import Receipt


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
    except Exception as e:
        receipt.status = "failed"
        receipt.error_message = str(e)

    await db.commit()
    await db.refresh(receipt)

    return receipt
