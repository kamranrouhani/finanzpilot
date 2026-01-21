"""Receipt model."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.shared.models import TimestampMixin, UUIDMixin


class Receipt(Base, UUIDMixin, TimestampMixin):
    """Receipt model for storing uploaded receipt images and OCR results."""

    __tablename__ = "receipts"

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # Will be used in Phase 2

    # File information
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(50), nullable=True)

    # OCR results
    ocr_raw_text = Column(Text, nullable=True)
    ocr_model = Column(String(50), nullable=True, default="qwen2.5-vl:7b")
    ocr_processed_at = Column(DateTime(timezone=True), nullable=True)

    # Extracted structured data (JSON)
    extracted_data = Column(JSONB, nullable=True)

    # Status
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Receipt(id={self.id}, filename={self.original_filename}, status={self.status})>"
