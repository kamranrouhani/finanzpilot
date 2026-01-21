"""Receipt routes."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.features.auth.models import User
from app.features.receipts.schemas import ReceiptListResponse, ReceiptResponse
from app.features.receipts.service import (create_receipt, get_user_receipts,
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
    # Validate file type
    if not file.content_type or not file.content_type.startswith(
        ("image/", "application/pdf")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image and PDF files are allowed",
        )

    # Save file
    stored_path, file_size = await save_receipt_file(
        file.file, file.filename or "unknown", str(current_user.id)
    )

    # Create receipt record
    receipt = await create_receipt(
        db,
        user_id=str(current_user.id),
        filename=file.filename or "unknown",
        stored_path=stored_path,
        file_size=file_size,
        mime_type=file.content_type,
    )

    # Process OCR (async in background would be better in production)
    receipt = await process_receipt_ocr(db, receipt)

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
    receipt_id: str,
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
