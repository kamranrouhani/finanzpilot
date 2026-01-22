"""Pydantic schemas for transactions."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    """Base schema for transaction."""

    # Core transaction data
    date: date
    amount: Decimal = Field(..., decimal_places=2)
    currency: str = Field(default="EUR", max_length=3)
    balance_after: Optional[Decimal] = Field(None, decimal_places=2)

    # Account info
    account_name: Optional[str] = Field(None, max_length=100)
    account_iban_last4: Optional[str] = Field(None, max_length=4)

    # Counterparty
    counterparty: Optional[str] = Field(None, max_length=255)
    counterparty_iban: Optional[str] = Field(None, max_length=34)

    # Description
    description: Optional[str] = None
    e_ref: Optional[str] = Field(None, max_length=100)
    mandate_ref: Optional[str] = Field(None, max_length=100)
    creditor_id: Optional[str] = Field(None, max_length=100)

    # Categorization
    category_id: Optional[UUID] = None
    subcategory_id: Optional[UUID] = None
    tax_category_id: Optional[UUID] = None

    # User additions
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction manually."""

    source: str = Field(default="manual", max_length=20)


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""

    category_id: Optional[UUID] = None
    subcategory_id: Optional[UUID] = None
    tax_category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""

    id: UUID
    user_id: UUID

    # Finanzguru metadata (preserved from import)
    fg_main_category: Optional[str] = None
    fg_subcategory: Optional[str] = None
    fg_contract_name: Optional[str] = None
    fg_contract_frequency: Optional[str] = None
    fg_contract_id: Optional[str] = None
    fg_is_transfer: bool = False
    fg_excluded_from_budget: bool = False
    fg_transaction_type: Optional[str] = None
    fg_analysis_amount: Optional[Decimal] = None
    fg_week: Optional[str] = None
    fg_month: Optional[str] = None
    fg_quarter: Optional[str] = None
    fg_year: Optional[str] = None

    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionImportRow(BaseModel):
    """Schema for a single row from Finanzguru XLSX import.

    Maps directly to Finanzguru export column names.
    """

    # Required fields
    Buchungstag: str  # Date (DD.MM.YYYY format)
    Betrag: str  # Amount (German decimal format: 1.234,56)

    # Account info
    Referenzkonto: Optional[str] = None  # Account name
    Name_Referenzkonto: Optional[str] = None  # Account display name
    Kontostand: Optional[str] = None  # Balance after transaction
    Waehrung: str = "EUR"  # Currency

    # Counterparty
    Beguenstigter_Auftraggeber: Optional[str] = None  # Counterparty name
    IBAN_Beguenstigter_Auftraggeber: Optional[str] = None  # Counterparty IBAN

    # Description
    Verwendungszweck: Optional[str] = None  # Transaction description
    E_Ref: Optional[str] = None  # E-Reference
    Mandatsreferenz: Optional[str] = None  # Mandate reference
    Glaeubiger_ID: Optional[str] = None  # Creditor ID

    # Finanzguru analysis
    Analyse_Hauptkategorie: Optional[str] = None
    Analyse_Unterkategorie: Optional[str] = None
    Analyse_Vertrag: Optional[str] = None
    Analyse_Vertragsturnus: Optional[str] = None
    Analyse_Vertrags_ID: Optional[str] = None
    Analyse_Umbuchung: Optional[str] = None  # "Ja" or empty
    Analyse_Vom_frei_verfuegbaren_Einkommen_ausgeschlossen: Optional[str] = None
    Analyse_Umsatzart: Optional[str] = None
    Analyse_Betrag: Optional[str] = None
    Analyse_Woche: Optional[str] = None
    Analyse_Monat: Optional[str] = None
    Analyse_Quartal: Optional[str] = None
    Analyse_Jahr: Optional[str] = None

    # User additions (from Finanzguru)
    Tags: Optional[str] = None  # Comma-separated
    Notiz: Optional[str] = None  # Notes


class TransactionImportRequest(BaseModel):
    """Schema for transaction import request."""

    # File will be uploaded separately
    skip_duplicates: bool = Field(default=True, description="Skip transactions that already exist")


class TransactionImportResponse(BaseModel):
    """Schema for transaction import response."""

    total_rows: int
    imported: int
    skipped: int
    errors: int
    error_details: Optional[List[str]] = None
