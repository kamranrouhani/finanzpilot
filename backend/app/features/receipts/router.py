"""Receipt routes."""
import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.features.auth.models import User
from app.features.receipts.schemas import ReceiptListResponse, ReceiptResponse
from app.features.receipts.service import (cleanup_receipt_file, create_receipt,
                                           get_user_receipts,
                                           process_receipt_ocr,
                                           save_receipt_file)
from app.shared.dependencies import get_current_user

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.post("", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReceiptResponse:
    """
    Upload a receipt image.

    Args:
        file: Uploaded file
        current_user: Current authenticated user
        db: Database session

    Returns:
        ReceiptResponse: Created receipt
    """
    # Validate file size
    if hasattr(file, 'size') and file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
        )

    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename",
        )

    file_extension = os.path.splitext(file.filename.lower())[1]
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Validate content type (additional check)
    allowed_content_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".pdf": "application/pdf"
    }

    expected_content_type = allowed_content_types.get(file_extension)
    if expected_content_type and file.content_type != expected_content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type mismatch. Expected {expected_content_type} for {file_extension} files",
        )

    # Save file
    stored_path, file_size = await save_receipt_file(
        file.file, file.filename or "unknown", str(current_user.id)
    )

    receipt = None
    try:
        # Create receipt record
        receipt = await create_receipt(
            db,
            user_id=str(current_user.id),
            filename=file.filename or "unknown",
            stored_path=stored_path,
            file_size=file_size,
            mime_type=file.content_type,
        )
    except Exception:
        # If database insert fails, clean up the saved file
        await cleanup_receipt_file(stored_path)
        raise

    try:
        # Process OCR (async in background would be better in production)
        receipt = await process_receipt_ocr(db, receipt)
    except Exception:
        # If OCR fails, keep the file and database record
        # The receipt status will be set to "failed" in process_receipt_ocr
        # User can retry OCR later
        pass

    return ReceiptResponse.model_validate(receipt)


@router.get("", response_model=ReceiptListResponse)
async def list_receipts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReceiptListResponse:
    """
    Get all receipts for current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        ReceiptListResponse: List of receipts
    """
    receipts = await get_user_receipts(db, str(current_user.id))

    return ReceiptListResponse(
        receipts=[ReceiptResponse.model_validate(r) for r in receipts],
        total=len(receipts),
    )


@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReceiptResponse:
    """
    Get a single receipt by ID.

    Args:
        receipt_id: Receipt ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ReceiptResponse: Receipt data
    """
    from sqlalchemy import select

    from app.features.receipts.models import Receipt

    result = await db.execute(
        select(Receipt).where(
            Receipt.id == receipt_id, Receipt.user_id == current_user.id
        )
    )
    receipt = result.scalar_one_or_none()

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found",
        )

    return ReceiptResponse.model_validate(receipt)
