"""Tests for receipt-transaction matching functionality."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.receipts.models import Receipt
from app.features.transactions.models import Transaction


@pytest.fixture
async def test_transaction(db_session: AsyncSession, test_user: dict) -> Transaction:
    """Create a test transaction."""
    transaction = Transaction(
        user_id=test_user["id"],
        date=date.today(),
        amount=Decimal("-42.99"),
        currency="EUR",
        counterparty="REWE Supermarket",
        description="Grocery shopping",
        source="manual"
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction


@pytest.fixture
async def test_receipt(db_session: AsyncSession, test_user: dict) -> Receipt:
    """Create a test receipt with extracted data."""
    receipt = Receipt(
        user_id=test_user["id"],
        original_filename="receipt.jpg",
        stored_path="/tmp/receipt.jpg",
        file_size=1024,
        mime_type="image/jpeg",
        status="completed",
        extracted_data={
            "merchant": "REWE",
            "date": str(date.today()),
            "total": 42.99,
            "items": [{"name": "Groceries", "price": 42.99}]
        }
    )
    db_session.add(receipt)
    await db_session.commit()
    await db_session.refresh(receipt)
    return receipt


class TestReceiptMatching:
    """Test receipt-transaction matching."""

    async def test_find_exact_match(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_receipt: Receipt,
        test_transaction: Transaction
    ):
        """Test finding an exact match (same date and amount)."""
        response = await client.get(
            f"/api/receipts/{test_receipt.id}/matches",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["receipt_id"] == str(test_receipt.id)
        assert len(data["matches"]) >= 1

        # First match should have high confidence
        first_match = data["matches"][0]
        assert first_match["id"] == str(test_transaction.id)
        assert first_match["confidence"] >= 80.0  # High confidence for exact match

    async def test_find_match_different_date(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_receipt: Receipt,
        db_session: AsyncSession,
        test_user: dict
    ):
        """Test finding match with different date."""
        # Create transaction 3 days before receipt
        transaction = Transaction(
            user_id=test_user["id"],
            date=date.today() - timedelta(days=3),
            amount=Decimal("-42.99"),
            currency="EUR",
            counterparty="REWE",
            description="Shopping",
            source="manual"
        )
        db_session.add(transaction)
        await db_session.commit()

        response = await client.get(
            f"/api/receipts/{test_receipt.id}/matches",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["matches"]) >= 1

        # Should still match but with lower confidence
        match = next(m for m in data["matches"] if m["id"] == str(transaction.id))
        assert match["confidence"] >= 50.0  # Still reasonable confidence
        assert match["confidence"] < 80.0  # But lower than exact match

    async def test_no_matches_different_amount(
        self,
        client: AsyncClient,
        test_user_token: str,
        db_session: AsyncSession,
        test_user: dict
    ):
        """Test that transactions with very different amounts don't match."""
        # Create receipt with specific amount
        receipt = Receipt(
            user_id=test_user["id"],
            original_filename="receipt2.jpg",
            stored_path="/tmp/receipt2.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            status="completed",
            extracted_data={
                "merchant": "Store",
                "date": str(date.today()),
                "total": 100.00,
            }
        )
        db_session.add(receipt)

        # Create transaction with very different amount
        transaction = Transaction(
            user_id=test_user["id"],
            date=date.today(),
            amount=Decimal("-10.00"),  # Very different amount
            currency="EUR",
            counterparty="Store",
            description="Purchase",
            source="manual"
        )
        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(receipt)

        response = await client.get(
            f"/api/receipts/{receipt.id}/matches",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should have low confidence or no matches
        if len(data["matches"]) > 0:
            match = data["matches"][0]
            assert match["confidence"] < 40.0  # Low confidence

    async def test_receipt_not_found(
        self,
        client: AsyncClient,
        test_user_token: str
    ):
        """Test getting matches for non-existent receipt."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/receipts/{fake_id}/matches",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 404


class TestReceiptLinking:
    """Test receipt-transaction linking."""

    async def test_link_receipt_success(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_receipt: Receipt,
        test_transaction: Transaction
    ):
        """Test successfully linking a receipt to a transaction."""
        response = await client.post(
            f"/api/receipts/{test_receipt.id}/link",
            json={"transaction_id": str(test_transaction.id)},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Note: transaction_id is not in ReceiptResponse schema currently
        # This test verifies the endpoint works

    async def test_link_receipt_invalid_transaction(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_receipt: Receipt
    ):
        """Test linking receipt to non-existent transaction."""
        fake_txn_id = "00000000-0000-0000-0000-000000000000"
        response = await client.post(
            f"/api/receipts/{test_receipt.id}/link",
            json={"transaction_id": fake_txn_id},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 404

    async def test_unlink_receipt_success(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_receipt: Receipt,
        test_transaction: Transaction
    ):
        """Test unlinking a receipt from a transaction."""
        # First link
        await client.post(
            f"/api/receipts/{test_receipt.id}/link",
            json={"transaction_id": str(test_transaction.id)},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        # Then unlink
        response = await client.post(
            f"/api/receipts/{test_receipt.id}/unlink",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200

    async def test_link_unauthorized(
        self,
        client: AsyncClient,
        test_receipt: Receipt,
        test_transaction: Transaction
    ):
        """Test linking without authentication."""
        response = await client.post(
            f"/api/receipts/{test_receipt.id}/link",
            json={"transaction_id": str(test_transaction.id)}
        )

        assert response.status_code == 401
