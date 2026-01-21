"""Finanzguru XLSX/CSV parser for importing transactions."""
import hashlib
import pandas as pd
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any
from pathlib import Path


# Column mapping from Finanzguru export to our internal field names
# Based on CLAUDE.md specification
FINANZGURU_COLUMN_MAPPING = {
    "Buchungstag": "date",
    "Referenzkonto": "account_iban",
    "Name Referenzkonto": "account_name",
    "Betrag": "amount",
    "Kontostand": "balance",
    "Waehrung": "currency",
    "Beguenstigter/Auftraggeber": "counterparty",
    "IBAN Beguenstigter/Auftraggeber": "counterparty_iban",
    "Verwendungszweck": "description",
    "E-Ref": "e_ref",
    "Mandatsreferenz": "mandate_ref",
    "Glaeubiger-ID": "creditor_id",
    "Analyse-Hauptkategorie": "category",
    "Analyse-Unterkategorie": "subcategory",
    "Analyse-Vertrag": "contract",
    "Analyse-Vertragsturnus": "contract_frequency",
    "Analyse-Vertrags-ID": "contract_id",
    "Analyse-Umbuchung": "is_transfer",
    "Analyse-Vom frei verfuegbaren Einkommen ausgeschlossen": "excluded_from_budget",
    "Analyse-Umsatzart": "transaction_type",
    "Analyse-Betrag": "analysis_amount",
    "Analyse-Woche": "week",
    "Analyse-Monat": "month",
    "Analyse-Quartal": "quarter",
    "Analyse-Jahr": "year",
    "Tags": "tags",
    "Notiz": "notes",
}

# Required columns for a valid import
REQUIRED_COLUMNS = [
    "Buchungstag",
    "Betrag",
    "Beguenstigter/Auftraggeber",
    "Verwendungszweck",
]


def parse_german_date(date_str: str) -> date:
    """
    Parse German date format DD.MM.YYYY.

    Args:
        date_str: Date string in DD.MM.YYYY format

    Returns:
        date object

    Raises:
        ValueError: If date format is invalid
    """
    if not date_str or pd.isna(date_str):
        raise ValueError("Date string cannot be empty")

    try:
        # Parse DD.MM.YYYY format
        day, month, year = date_str.strip().split(".")
        return date(int(year), int(month), int(day))
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid date format '{date_str}'. Expected DD.MM.YYYY") from e


def parse_german_amount(amount_str: str) -> Decimal:
    """
    Parse German decimal format with comma as decimal separator.
    Examples: "-45,67", "2.500,00", "1.234,56"

    Args:
        amount_str: Amount string in German format

    Returns:
        Decimal amount

    Raises:
        ValueError: If amount format is invalid
    """
    if not amount_str or pd.isna(amount_str):
        raise ValueError("Amount string cannot be empty")

    try:
        # Remove thousands separator (dot) and replace decimal comma with dot
        cleaned = str(amount_str).strip().replace(".", "").replace(",", ".")
        return Decimal(cleaned)
    except (ValueError, InvalidOperation) as e:
        raise ValueError(f"Invalid amount format '{amount_str}'") from e


def parse_german_boolean(bool_str: str) -> bool:
    """
    Parse German boolean values.

    Args:
        bool_str: String like "Ja", "Nein", "True", "False"

    Returns:
        Boolean value
    """
    if pd.isna(bool_str) or not bool_str:
        return False

    bool_str = str(bool_str).strip().lower()
    return bool_str in ("ja", "yes", "true", "1", "wahr")


def generate_import_hash(
    transaction_date: date,
    amount: Decimal,
    counterparty: str,
    description: str
) -> str:
    """
    Generate SHA-256 hash for duplicate detection.

    Args:
        transaction_date: Transaction date
        amount: Transaction amount
        counterparty: Counterparty name
        description: Transaction description

    Returns:
        64-character hexadecimal hash string
    """
    # Combine key fields that uniquely identify a transaction
    data = f"{transaction_date}|{amount}|{counterparty}|{description}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def parse_finanzguru_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse Finanzguru XLSX or CSV export file.

    Args:
        file_path: Path to XLSX or CSV file

    Returns:
        List of transaction dictionaries ready for database import

    Raises:
        ValueError: If file format is invalid or required columns are missing
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read file based on extension
    if file_path.suffix.lower() == '.xlsx':
        df = pd.read_excel(file_path, engine='openpyxl')
    elif file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    # Validate required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Parse each row into a transaction dict
    transactions = []

    for idx, row in df.iterrows():
        try:
            # Parse core fields
            transaction_date = parse_german_date(row.get("Buchungstag"))
            amount = parse_german_amount(row.get("Betrag"))

            # Handle counterparty - check for NaN to avoid "nan" strings
            counterparty_value = row.get("Beguenstigter/Auftraggeber", "")
            counterparty = "" if pd.isna(counterparty_value) else str(counterparty_value).strip()

            # Handle description - check for NaN to avoid "nan" strings
            description_value = row.get("Verwendungszweck", "")
            description = "" if pd.isna(description_value) else str(description_value).strip()

            # Generate import hash for duplicate detection
            import_hash = generate_import_hash(
                transaction_date, amount, counterparty, description
            )

            # Build transaction dict
            transaction = {
                "date": transaction_date,
                "amount": amount,
                "counterparty": counterparty,
                "description": description,
                "import_hash": import_hash,
                "source": "finanzguru",
            }

            # Map all other columns
            for fg_col, our_field in FINANZGURU_COLUMN_MAPPING.items():
                if fg_col in df.columns and fg_col not in REQUIRED_COLUMNS:
                    value = row.get(fg_col)

                    # Skip if empty/NaN
                    if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                        continue

                    # Special handling for specific fields
                    if our_field in ("is_transfer", "excluded_from_budget"):
                        transaction[f"fg_{our_field}"] = parse_german_boolean(value)
                    elif our_field in ("contract", "contract_frequency", "contract_id",
                                      "transaction_type", "week", "month", "quarter", "year"):
                        # Finanzguru-specific fields
                        transaction[f"fg_{our_field}"] = str(value).strip()
                    elif our_field == "tags":
                        # Keep tags as string for now, will be converted to array in DB
                        transaction["tags"] = str(value).strip() if value else None
                    elif our_field == "category":
                        transaction["category"] = str(value).strip()
                    elif our_field == "subcategory":
                        transaction["subcategory"] = str(value).strip()
                    else:
                        # All other fields
                        transaction[our_field] = str(value).strip()

            transactions.append(transaction)

        except Exception as e:
            # Log error but continue processing other rows
            print(f"Warning: Failed to parse row {idx}: {e}")
            continue

    return transactions


def validate_import_data(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate parsed import data and generate statistics.

    Args:
        transactions: List of parsed transactions

    Returns:
        Dictionary with validation results and statistics
    """
    stats = {
        "total_count": len(transactions),
        "valid_count": 0,
        "invalid_count": 0,
        "errors": [],
    }

    required_fields = ["date", "amount", "import_hash"]

    for idx, transaction in enumerate(transactions):
        # Check required fields
        missing = [f for f in required_fields if f not in transaction]
        if missing:
            stats["invalid_count"] += 1
            stats["errors"].append({
                "row": idx,
                "error": f"Missing required fields: {missing}"
            })
        else:
            stats["valid_count"] += 1

    return stats
