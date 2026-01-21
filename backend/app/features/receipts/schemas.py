"""Pydantic schemas for receipts."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReceiptResponse(BaseModel):
    """Schema for receipt response."""

    id: UUID
    user_id: UUID
    original_filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    status: str
    ocr_raw_text: Optional[str]
    ocr_model: Optional[str]
    ocr_processed_at: Optional[datetime]
    extracted_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReceiptListResponse(BaseModel):
    """Schema for list of receipts."""

    receipts: list[ReceiptResponse]
    total: int
