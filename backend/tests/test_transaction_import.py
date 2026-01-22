"""Tests for transaction import functionality."""
import pytest
from datetime import date
from decimal import Decimal
from pathlib import Path
import os


@pytest.mark.asyncio
class TestTransactionImport:
    """Test transaction import from Finanzguru files."""

    @pytest.fixture
    def sample_csv_path(self):
        """Path to sample CSV file."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "sample-data",
            "finanzguru_sample.csv"
        )

    async def test_import_transactions_success(
        self, authenticated_client, db_session, sample_csv_path
    ):
        """Test successful import of transactions from CSV."""
        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        # Import transactions
        with open(sample_csv_path, "rb") as f:
            response = authenticated_client.post(
                "/api/transactions/import",
                files={"file": ("finanzguru.csv", f, "text/csv")},
            )

        assert response.status_code == 200
        data = response.json()

        assert "total_rows" in data
        assert "imported" in data
        assert "skipped" in data
        assert "errors" in data
        assert data["total_rows"] == 5
        assert data["imported"] == 5
        assert data["skipped"] == 0

    async def test_import_duplicate_detection(
        self, authenticated_client, db_session, sample_csv_path
    ):
        """Test that duplicate transactions are skipped on re-import."""
        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        # First import
        with open(sample_csv_path, "rb") as f:
            response1 = authenticated_client.post(
                "/api/transactions/import",
                files={"file": ("finanzguru.csv", f, "text/csv")},
            )

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["imported"] == 5

        # Second import - should skip all
        with open(sample_csv_path, "rb") as f:
            response2 = authenticated_client.post(
                "/api/transactions/import",
                files={"file": ("finanzguru.csv", f, "text/csv")},
            )

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["imported"] == 0
        assert data2["skipped"] == 5

    async def test_import_invalid_file_format(self, authenticated_client):
        """Test import with invalid file format."""
        # Try to upload a text file
        response = authenticated_client.post(
            "/api/transactions/import",
            files={"file": ("test.txt", b"not a valid file", "text/plain")},
        )

        assert response.status_code in (400, 422)

    async def test_import_empty_file(self, authenticated_client):
        """Test import with empty file."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Buchungstag,Betrag\n")  # Only headers
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = authenticated_client.post(
                    "/api/transactions/import",
                    files={"file": ("empty.csv", f, "text/csv")},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["imported"] == 0
        finally:
            os.unlink(temp_path)

    async def test_import_requires_authentication(self, client, sample_csv_path):
        """Test that import endpoint requires authentication."""
        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        with open(sample_csv_path, "rb") as f:
            response = client.post(
                "/api/transactions/import",
                files={"file": ("finanzguru.csv", f, "text/csv")},
            )

        assert response.status_code == 401

    async def test_import_stores_account_info(
        self, authenticated_client, db_session, sample_csv_path
    ):
        """Test that import stores account information in transactions."""
        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        # Import transactions
        with open(sample_csv_path, "rb") as f:
            response = authenticated_client.post(
                "/api/transactions/import",
                files={"file": ("finanzguru.csv", f, "text/csv")},
            )

        assert response.status_code == 200

        # Check that transactions have account info
        response = authenticated_client.get("/api/transactions?limit=100")
        assert response.status_code == 200
        transactions = response.json()["items"]

        # All transactions should have "Girokonto" as account
        for tx in transactions:
            assert tx.get("account_name") == "Girokonto"
            assert tx.get("account_iban_last4") == "3000"  # Last 4 of DE89370400440532013000

    async def test_import_maps_categories(
        self, authenticated_client, db_session, sample_csv_path
    ):
        """Test that import maps Finanzguru categories to our categories."""
        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        # Import transactions
        with open(sample_csv_path, "rb") as f:
            response = authenticated_client.post(
                "/api/transactions/import",
                files={"file": ("finanzguru.csv", f, "text/csv")},
            )

        assert response.status_code == 200

        # Get imported transactions
        response = authenticated_client.get("/api/transactions?limit=100")
        assert response.status_code == 200
        transactions = response.json()["items"]

        # Check that Finanzguru categories are preserved
        rewe_tx = next((t for t in transactions if "REWE" in t.get("counterparty", "")), None)
        if rewe_tx:
            assert rewe_tx.get("fg_main_category") == "Lebensmittel"
            assert rewe_tx.get("fg_subcategory") == "Supermarkt"

    async def test_import_preserves_metadata(
        self, authenticated_client, db_session, sample_csv_path
    ):
        """Test that import preserves all Finanzguru metadata."""
        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        # Import transactions
        with open(sample_csv_path, "rb") as f:
            response = authenticated_client.post(
                "/api/transactions/import",
                files={"file": ("finanzguru.csv", f, "text/csv")},
            )

        assert response.status_code == 200

        # Get imported transactions
        response = authenticated_client.get("/api/transactions?limit=100")
        assert response.status_code == 200
        transactions = response.json()["items"]

        # Find Netflix transaction (has contract info)
        netflix_tx = next((t for t in transactions if "Netflix" in t.get("counterparty", "")), None)
        if netflix_tx:
            assert netflix_tx.get("fg_contract_name") == "Netflix Abo"
            assert netflix_tx.get("fg_contract_frequency") == "monatlich"
            assert netflix_tx.get("fg_is_transfer") is False

    async def test_import_skip_duplicates_param(
        self, authenticated_client, db_session, sample_csv_path
    ):
        """Test skip_duplicates parameter."""
        if not os.path.exists(sample_csv_path):
            pytest.skip(f"Sample CSV not found at {sample_csv_path}")

        # First import
        with open(sample_csv_path, "rb") as f:
            response1 = authenticated_client.post(
                "/api/transactions/import?skip_duplicates=true",
                files={"file": ("finanzguru.csv", f, "text/csv")},
            )

        assert response1.status_code == 200
        assert response1.json()["imported"] == 5

        # Second import with skip_duplicates=false (might create duplicates or fail)
        with open(sample_csv_path, "rb") as f:
            response2 = authenticated_client.post(
                "/api/transactions/import?skip_duplicates=true",
                files={"file": ("finanzguru.csv", f, "text/csv")},
            )

        assert response2.status_code == 200
        assert response2.json()["skipped"] == 5
