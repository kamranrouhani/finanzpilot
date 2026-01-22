"""Tests for Finanzguru XLSX parser."""
import pytest
from datetime import date
from decimal import Decimal
import tempfile
import os

# We'll import the parser once it's created
# from app.features.transactions.finanzguru_parser import parse_finanzguru_xlsx


class TestFinanzguruParser:
    """Test Finanzguru XLSX parsing functionality."""

    @pytest.fixture
    def sample_csv_path(self):
        """Path to sample CSV file."""
        # Use the CSV file we created in sample-data
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "sample-data",
            "finanzguru_sample.csv"
        )

    def test_parse_german_date_format(self):
        """Test parsing German date format DD.MM.YYYY."""
        from app.features.transactions.finanzguru_parser import parse_german_date

        assert parse_german_date("15.01.2024") == date(2024, 1, 15)
        assert parse_german_date("01.12.2023") == date(2023, 12, 1)
        assert parse_german_date("29.02.2024") == date(2024, 2, 29)  # Leap year

    def test_parse_german_date_invalid(self):
        """Test parsing invalid date formats."""
        from app.features.transactions.finanzguru_parser import parse_german_date

        with pytest.raises(ValueError):
            parse_german_date("2024-01-15")  # Wrong format

        with pytest.raises(ValueError):
            parse_german_date("32.01.2024")  # Invalid day

    def test_parse_german_amount(self):
        """Test parsing German decimal format with comma."""
        from app.features.transactions.finanzguru_parser import parse_german_amount

        assert parse_german_amount("-45,67") == Decimal("-45.67")
        assert parse_german_amount("2.500,00") == Decimal("2500.00")
        assert parse_german_amount("1.234,56") == Decimal("1234.56")
        assert parse_german_amount("-12,99") == Decimal("-12.99")
        assert parse_german_amount("0,00") == Decimal("0.00")

    def test_parse_german_amount_invalid(self):
        """Test parsing invalid amount formats."""
        from app.features.transactions.finanzguru_parser import parse_german_amount

        with pytest.raises(ValueError):
            parse_german_amount("invalid")

        with pytest.raises(ValueError):
            parse_german_amount("")

    def test_generate_import_hash(self):
        """Test generating consistent hash for duplicate detection."""
        from app.features.transactions.finanzguru_parser import generate_import_hash

        # Same data should produce same hash
        hash1 = generate_import_hash(
            date(2024, 1, 15),
            Decimal("-45.67"),
            "REWE Markt GmbH",
            "REWE SAGT DANKE 2024-01-15"
        )
        hash2 = generate_import_hash(
            date(2024, 1, 15),
            Decimal("-45.67"),
            "REWE Markt GmbH",
            "REWE SAGT DANKE 2024-01-15"
        )
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hash

        # Different data should produce different hash
        hash3 = generate_import_hash(
            date(2024, 1, 14),
            Decimal("-45.67"),
            "REWE Markt GmbH",
            "REWE SAGT DANKE 2024-01-15"
        )
        assert hash1 != hash3

    def test_parse_csv_file(self, sample_csv_path):
        """Test parsing the sample CSV file."""
        from app.features.transactions.finanzguru_parser import parse_finanzguru_file

        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        transactions = parse_finanzguru_file(sample_csv_path)

        # Should parse 5 transactions
        assert len(transactions) == 5

        # Check first transaction (REWE)
        t1 = transactions[0]
        assert t1["date"] == date(2024, 1, 15)
        assert t1["amount"] == Decimal("-45.67")
        assert t1["counterparty"] == "REWE Markt GmbH"
        assert t1["description"] == "REWE SAGT DANKE 2024-01-15"
        assert t1["category"] == "Lebensmittel"
        assert t1["subcategory"] == "Supermarkt"
        assert t1["currency"] == "EUR"
        assert "import_hash" in t1

        # Check second transaction (Netflix)
        t2 = transactions[1]
        assert t2["date"] == date(2024, 1, 14)
        assert t2["amount"] == Decimal("-12.99")
        assert t2["counterparty"] == "Netflix"
        assert t2["fg_contract"] == "Netflix Abo"
        assert t2["fg_contract_frequency"] == "monatlich"

        # Check third transaction (Salary - income)
        t3 = transactions[2]
        assert t3["date"] == date(2024, 1, 12)
        assert t3["amount"] == Decimal("2500.00")
        assert t3["counterparty"] == "Arbeitgeber GmbH"
        assert t3["category"] == "Einnahmen"

    def test_parse_empty_file(self):
        """Test parsing empty file."""
        from app.features.transactions.finanzguru_parser import parse_finanzguru_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write only headers
            f.write("Buchungstag,Betrag\n")
            temp_path = f.name

        try:
            transactions = parse_finanzguru_file(temp_path)
            assert len(transactions) == 0
        finally:
            os.unlink(temp_path)

    def test_parse_file_with_missing_columns(self):
        """Test parsing file with missing required columns."""
        from app.features.transactions.finanzguru_parser import parse_finanzguru_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Missing required columns
            f.write("SomeColumn,AnotherColumn\n")
            f.write("value1,value2\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing required columns"):
                parse_finanzguru_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_column_mapping(self):
        """Test that all Finanzguru columns are properly mapped."""
        from app.features.transactions.finanzguru_parser import FINANZGURU_COLUMN_MAPPING

        # Verify critical columns exist in mapping
        required_cols = [
            "Buchungstag",
            "Betrag",
            "Beguenstigter/Auftraggeber",
            "Verwendungszweck",
            "Analyse-Hauptkategorie",
            "Analyse-Unterkategorie",
        ]

        for col in required_cols:
            assert col in FINANZGURU_COLUMN_MAPPING

        # Verify mappings are correct
        assert FINANZGURU_COLUMN_MAPPING["Buchungstag"] == "date"
        assert FINANZGURU_COLUMN_MAPPING["Betrag"] == "amount"
        assert FINANZGURU_COLUMN_MAPPING["Beguenstigter/Auftraggeber"] == "counterparty"

    def test_parse_transaction_with_tags(self, sample_csv_path):
        """Test parsing transaction with tags."""
        from app.features.transactions.finanzguru_parser import parse_finanzguru_file

        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        transactions = parse_finanzguru_file(sample_csv_path)

        # Netflix transaction has tags
        netflix = transactions[1]
        assert "tags" in netflix
        # Tags should be parsed (either as list or string depending on implementation)

    def test_parse_boolean_fields(self, sample_csv_path):
        """Test parsing boolean fields from Finanzguru export."""
        from app.features.transactions.finanzguru_parser import parse_finanzguru_file

        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        transactions = parse_finanzguru_file(sample_csv_path)

        # Check fg_is_transfer (Analyse-Umbuchung)
        assert transactions[0]["fg_is_transfer"] is False

        # Check fg_excluded_from_budget
        assert transactions[2]["fg_excluded_from_budget"] is True  # Salary
        assert transactions[0]["fg_excluded_from_budget"] is False  # REWE

    def test_empty_counterparty_description_become_empty_strings_not_nan(self):
        """Test that empty counterparty and description fields become empty strings, not 'nan'."""
        import pandas as pd
        from app.features.transactions.finanzguru_parser import parse_finanzguru_file

        # Create test data with empty counterparty and description (represented as NaN)
        test_data = {
            "Buchungstag": ["15.01.2024"],
            "Betrag": ["-45,67"],
            "Beguenstigter/Auftraggeber": [pd.NA],  # Empty cell becomes NaN
            "Verwendungszweck": [pd.NA],  # Empty cell becomes NaN
        }
        df = pd.DataFrame(test_data)

        # Temporarily write to a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            test_file = f.name

        try:
            transactions = parse_finanzguru_file(test_file)

            assert len(transactions) == 1
            t = transactions[0]

            # These should be empty strings, not "nan"
            assert t["counterparty"] == ""
            assert t["description"] == ""

        finally:
            os.unlink(test_file)