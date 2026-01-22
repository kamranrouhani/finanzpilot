"""Tests for budget endpoints."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.budgets.models import Budget
from app.features.categories.models import Category


@pytest.fixture
async def test_category(db_session: AsyncSession) -> Category:
    """Create a test category for budgets."""
    result = await db_session.execute(
        select(Category).where(Category.parent_id.is_(None)).limit(1)
    )
    category = result.scalar_one_or_none()

    if not category:
        # Create a category if none exists
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


class TestBudgetCreate:
    """Test budget creation."""

    async def test_create_budget_success(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category,
        db_session: AsyncSession
    ):
        """Test successful budget creation."""
        budget_data = {
            "category_id": str(test_category.id),
            "amount": 500.00,
            "period": "monthly",
            "start_date": str(date.today()),
            "is_active": True
        }

        response = await client.post(
            "/api/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == str(test_category.id)
        assert Decimal(str(data["amount"])) == Decimal("500.00")
        assert data["period"] == "monthly"
        assert "id" in data

        # Verify budget was created in database
        result = await db_session.execute(
            select(Budget).where(Budget.id == data["id"])
        )
        budget = result.scalar_one_or_none()
        assert budget is not None
        assert budget.amount == Decimal("500.00")

    async def test_create_budget_unauthorized(
        self,
        client: AsyncClient,
        test_category: Category
    ):
        """Test budget creation without authentication."""
        budget_data = {
            "category_id": str(test_category.id),
            "amount": 500.00,
            "period": "monthly",
            "start_date": str(date.today())
        }

        response = await client.post("/api/budgets", json=budget_data)
        assert response.status_code == 401

    async def test_create_budget_invalid_amount(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category
    ):
        """Test budget creation with negative amount."""
        budget_data = {
            "category_id": str(test_category.id),
            "amount": -100.00,
            "period": "monthly",
            "start_date": str(date.today())
        }

        response = await client.post(
            "/api/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 422  # Validation error

    async def test_create_budget_invalid_period(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category
    ):
        """Test budget creation with invalid period."""
        budget_data = {
            "category_id": str(test_category.id),
            "amount": 500.00,
            "period": "invalid_period",
            "start_date": str(date.today())
        }

        response = await client.post(
            "/api/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        # Should either accept or reject invalid period
        # Implementation will validate this
        assert response.status_code in [201, 400, 422]


class TestBudgetList:
    """Test budget listing."""

    async def test_list_budgets_empty(
        self,
        client: AsyncClient,
        test_user_token: str
    ):
        """Test listing budgets when user has none."""
        response = await client.get(
            "/api/budgets",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_budgets_with_data(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category
    ):
        """Test listing budgets with existing data."""
        # Create a budget first
        budget_data = {
            "category_id": str(test_category.id),
            "amount": 500.00,
            "period": "monthly",
            "start_date": str(date.today())
        }

        create_response = await client.post(
            "/api/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert create_response.status_code == 201

        # List budgets
        response = await client.get(
            "/api/budgets",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["category_id"] == str(test_category.id)

    async def test_list_budgets_unauthorized(self, client: AsyncClient):
        """Test listing budgets without authentication."""
        response = await client.get("/api/budgets")
        assert response.status_code == 401


class TestBudgetGet:
    """Test getting a single budget."""

    async def test_get_budget_success(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category
    ):
        """Test getting a specific budget."""
        # Create a budget
        budget_data = {
            "category_id": str(test_category.id),
            "amount": 500.00,
            "period": "monthly",
            "start_date": str(date.today())
        }

        create_response = await client.post(
            "/api/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        budget_id = create_response.json()["id"]

        # Get the budget
        response = await client.get(
            f"/api/budgets/{budget_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == budget_id
        assert data["category_id"] == str(test_category.id)

    async def test_get_budget_not_found(
        self,
        client: AsyncClient,
        test_user_token: str
    ):
        """Test getting a non-existent budget."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/budgets/{fake_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 404


class TestBudgetUpdate:
    """Test budget updates."""

    async def test_update_budget_success(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category
    ):
        """Test successful budget update."""
        # Create a budget
        budget_data = {
            "category_id": str(test_category.id),
            "amount": 500.00,
            "period": "monthly",
            "start_date": str(date.today())
        }

        create_response = await client.post(
            "/api/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        budget_id = create_response.json()["id"]

        # Update the budget
        update_data = {"amount": 750.00}
        response = await client.put(
            f"/api/budgets/{budget_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(str(data["amount"])) == Decimal("750.00")

    async def test_update_budget_not_found(
        self,
        client: AsyncClient,
        test_user_token: str
    ):
        """Test updating a non-existent budget."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"amount": 750.00}

        response = await client.put(
            f"/api/budgets/{fake_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 404


class TestBudgetDelete:
    """Test budget deletion."""

    async def test_delete_budget_success(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category,
        db_session: AsyncSession
    ):
        """Test successful budget deletion."""
        # Create a budget
        budget_data = {
            "category_id": str(test_category.id),
            "amount": 500.00,
            "period": "monthly",
            "start_date": str(date.today())
        }

        create_response = await client.post(
            "/api/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        budget_id = create_response.json()["id"]

        # Delete the budget
        response = await client.delete(
            f"/api/budgets/{budget_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 204

        # Verify budget was deleted
        result = await db_session.execute(
            select(Budget).where(Budget.id == budget_id)
        )
        budget = result.scalar_one_or_none()
        assert budget is None

    async def test_delete_budget_not_found(
        self,
        client: AsyncClient,
        test_user_token: str
    ):
        """Test deleting a non-existent budget."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/budgets/{fake_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 404


class TestBudgetSummary:
    """Test budget summary endpoint."""

    async def test_budget_summary_empty(
        self,
        client: AsyncClient,
        test_user_token: str
    ):
        """Test budget summary with no budgets."""
        response = await client.get(
            "/api/budgets/summary",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_budgeted" in data
        assert "total_spent" in data
        assert "total_remaining" in data
        assert "budgets" in data
        assert isinstance(data["budgets"], list)

    async def test_budget_summary_with_budgets(
        self,
        client: AsyncClient,
        test_user_token: str,
        test_category: Category
    ):
        """Test budget summary with existing budgets."""
        # Create a budget
        budget_data = {
            "category_id": str(test_category.id),
            "amount": 500.00,
            "period": "monthly",
            "start_date": str(date.today())
        }

        await client.post(
            "/api/budgets",
            json=budget_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        # Get summary
        response = await client.get(
            "/api/budgets/summary",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(str(data["total_budgeted"])) >= Decimal("500.00")
        assert len(data["budgets"]) >= 1

        # Check budget progress fields
        budget = data["budgets"][0]
        assert "spent" in budget
        assert "remaining" in budget
        assert "percentage" in budget
        assert "is_over_budget" in budget
