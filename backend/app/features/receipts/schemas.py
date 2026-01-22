"""Pydantic schemas for receipts."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReceiptResponse(BaseModel):
    """Schema for receipt response."""

    id: UUID
    user_id: UUID
    transaction_id: Optional[UUID] = None
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


class TransactionMatch(BaseModel):
    """Schema for a matched transaction."""

    id: UUID
    date: str
    amount: str
    counterparty: Optional[str]
    description: Optional[str]
    confidence: float = Field(..., ge=0, le=100, description="Confidence score 0-100")

    model_config = {"from_attributes": True}


class ReceiptMatchesResponse(BaseModel):
    """Schema for receipt matching results."""

    receipt_id: UUID
    matches: list[TransactionMatch]


class LinkReceiptRequest(BaseModel):
    """Schema for linking receipt to transaction."""

    transaction_id: UUID
