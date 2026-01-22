"""Pydantic schemas for AI features."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CategorySuggestionRequest(BaseModel):
    """Request for category suggestion."""

    counterparty: Optional[str] = None
    description: Optional[str] = None
    amount: float


class CategorySuggestion(BaseModel):
    """AI category suggestion response."""

    category: str
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    reasoning: Optional[str] = None


class BulkCategorizationRequest(BaseModel):
    """Request for bulk categorization of transactions."""

    transaction_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class TransactionCategorization(BaseModel):
    """Categorization result for a single transaction."""

    transaction_id: UUID
    suggested_category: Optional[str]
    confidence: float
    error: Optional[str] = None


class BulkCategorizationResponse(BaseModel):
    """Response for bulk categorization."""

    results: list[TransactionCategorization]
    total: int
    successful: int
    failed: int


class SpendingInsight(BaseModel):
    """A single spending insight."""

    type: str = Field(..., description="Type: increase, decrease, anomaly, pattern")
    category: Optional[str] = None
    message: str
    severity: str = Field(default="info", description="info, warning, or critical")


class InsightsResponse(BaseModel):
    """Response with spending insights and recommendations."""

    insights: list[SpendingInsight]
    recommendations: list[str]


class ChatRequest(BaseModel):
    """Natural language chat request."""

    message: str = Field(..., min_length=1, max_length=500)
    language: str = Field(default="en", description="Response language: en or de")


class ChatResponse(BaseModel):
    """Chat response."""

    answer: str
    context_used: bool = Field(..., description="Whether transaction data was used")
