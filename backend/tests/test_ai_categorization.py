"""Tests for AI categorization features."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.features.transactions.models import Transaction
from app.features.categories.models import Category
from decimal import Decimal


@pytest.fixture
async def test_category(db_session: AsyncSession) -> Category:
    """Get or create a test category."""
    from sqlalchemy import select

    result = await db_session.execute(
        select(Category).where(Category.name == "Groceries").limit(1)
    )
    category = result.scalar_one_or_none()

    if not category:
        category = Category(
            name="Groceries",
            name_de="Lebensmittel",
            is_income=False,
            icon="shopping-cart",
            color="#16A34A",
            sort_order=1
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

    return category


@pytest.fixture
async def uncategorized_transaction(
    db_session: AsyncSession,
    test_user: dict
) -> Transaction:
    """Create an uncategorized transaction."""
    transaction = Transaction(
        user_id=test_user["id"],
        date="2026-01-22",
        amount=Decimal("-25.50"),
        currency="EUR",
        counterparty="REWE Supermarket",
        description="Grocery shopping",
        source="manual"
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction


class TestCategorySuggestion:
    """Test AI category suggestion."""

    @patch('app.features.ai.service.ollama_client.generate')
    async def test_suggest_category_success(
        self,
        mock_generate: AsyncMock,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category
    ):
        """Test successful category suggestion with mocked Ollama."""
        # Mock Ollama response
        mock_generate.return_value = {
            "response": '{"category": "Groceries", "confidence": 0.95, "reasoning": "Counterparty is REWE, a supermarket chain"}',
            "model": "qwen2.5:7b"
        }

        request_data = {
            "counterparty": "REWE Supermarket",
            "description": "Grocery shopping",
            "amount": -25.50
        }

        response = await client.post(
            "/api/ai/categorize",
            json=request_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Groceries"
        assert data["confidence"] >= 0.9
        assert "reasoning" in data

        # Verify Ollama was called
        mock_generate.assert_called_once()

    @patch('app.features.ai.service.ollama_client.generate')
    async def test_suggest_category_ollama_failure(
        self,
        mock_generate: AsyncMock,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category
    ):
        """Test category suggestion with Ollama failure (should return fallback)."""
        # Mock Ollama failure
        mock_generate.side_effect = ValueError("Ollama connection failed")

        request_data = {
            "counterparty": "Some Store",
            "description": "Purchase",
            "amount": -10.00
        }

        response = await client.post(
            "/api/ai/categorize",
            json=request_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        # Should return fallback category with low confidence
        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] <= 0.2  # Low confidence for fallback
        assert "category" in data

    async def test_suggest_category_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test category suggestion without authentication."""
        request_data = {
            "counterparty": "Store",
            "description": "Purchase",
            "amount": -10.00
        }

        response = await client.post(
            "/api/ai/categorize",
            json=request_data
        )

        assert response.status_code == 401


class TestBulkCategorization:
    """Test bulk categorization."""

    @patch('app.features.ai.service.ollama_client.generate')
    async def test_bulk_categorize_success(
        self,
        mock_generate: AsyncMock,
        client: AsyncClient,
        test_user_token: str,
        uncategorized_transaction: Transaction,
        test_category: Category
    ):
        """Test bulk categorization with mocked Ollama."""
        # Mock Ollama response
        mock_generate.return_value = {
            "response": '{"category": "Groceries", "confidence": 0.85, "reasoning": "Supermarket purchase"}',
            "model": "qwen2.5:7b"
        }

        request_data = {
            "transaction_ids": [str(uncategorized_transaction.id)]
        }

        response = await client.post(
            "/api/ai/categorize/bulk",
            json=request_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["successful"] >= 0
        assert len(data["results"]) == 1
        assert data["results"][0]["transaction_id"] == str(uncategorized_transaction.id)

    async def test_bulk_categorize_empty_list(
        self,
        client: AsyncClient,
        test_user_token: str
    ):
        """Test bulk categorization with empty transaction list."""
        request_data = {
            "transaction_ids": []
        }

        response = await client.post(
            "/api/ai/categorize/bulk",
            json=request_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 400

    @patch('app.features.ai.service.ollama_client.generate')
    async def test_bulk_categorize_nonexistent_transaction(
        self,
        mock_generate: AsyncMock,
        client: AsyncClient,
        test_user_token: str
    ):
        """Test bulk categorization with non-existent transaction."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        request_data = {
            "transaction_ids": [fake_id]
        }

        response = await client.post(
            "/api/ai/categorize/bulk",
            json=request_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["failed"] == 1
        assert data["results"][0]["error"] is not None
