"""Transaction model."""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.shared.models import TimestampMixin, UUIDMixin


class Transaction(Base, UUIDMixin, TimestampMixin):
    """Transaction model for financial transactions.

    Supports Finanzguru import format with all metadata fields.
    """

    __tablename__ = "transactions"

    # User ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Account information
    account_name = Column(String(100), nullable=True)
    account_iban_last4 = Column(String(4), nullable=True)

    # Core transaction data
    date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=True)  # Kontostand

    # Counterparty
    counterparty = Column(String(255), nullable=True)
    counterparty_iban = Column(String(34), nullable=True)

    # Description and references
    description = Column(Text, nullable=True)  # Verwendungszweck
    e_ref = Column(String(100), nullable=True)  # E-Ref
    mandate_ref = Column(String(100), nullable=True)  # Mandatsreferenz
    creditor_id = Column(String(100), nullable=True)  # Glaeubiger-ID

    # Categorization
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    subcategory_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    tax_category_id = Column(UUID(as_uuid=True), ForeignKey("tax_categories.id"), nullable=True)

    # Finanzguru analysis metadata (preserved from import)
    fg_main_category = Column(String(100), nullable=True)  # Analyse-Hauptkategorie
    fg_subcategory = Column(String(100), nullable=True)  # Analyse-Unterkategorie
    fg_contract_name = Column(String(100), nullable=True)  # Analyse-Vertrag
    fg_contract_frequency = Column(String(20), nullable=True)  # Analyse-Vertragsturnus
    fg_contract_id = Column(String(50), nullable=True)  # Analyse-Vertrags-ID
    fg_is_transfer = Column(Boolean, default=False, nullable=False)  # Analyse-Umbuchung
    fg_excluded_from_budget = Column(Boolean, default=False, nullable=False)  # Vom Budget ausgeschlossen
    fg_transaction_type = Column(String(50), nullable=True)  # Analyse-Umsatzart
    fg_analysis_amount = Column(Numeric(12, 2), nullable=True)  # Analyse-Betrag

    # Time analysis (from Finanzguru)
    fg_week = Column(String(10), nullable=True)  # Analyse-Woche
    fg_month = Column(String(10), nullable=True)  # Analyse-Monat
    fg_quarter = Column(String(10), nullable=True)  # Analyse-Quartal
    fg_year = Column(String(10), nullable=True)  # Analyse-Jahr

    # User additions
    tags = Column(ARRAY(Text), nullable=True)  # User-defined tags
    notes = Column(Text, nullable=True)  # User notes

    # Import tracking
    source = Column(String(20), default="manual", nullable=False)  # "manual", "finanzguru"
    import_hash = Column(String(64), nullable=True, index=True)  # For duplicate detection

    # Relationships
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", foreign_keys=[category_id])
    subcategory = relationship("Category", foreign_keys=[subcategory_id])
    tax_category = relationship("TaxCategory")

    # Unique constraint for import_hash per user
    __table_args__ = (
        UniqueConstraint('user_id', 'import_hash', name='uq_user_import_hash'),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, date={self.date}, amount={self.amount}, counterparty={self.counterparty})>"
