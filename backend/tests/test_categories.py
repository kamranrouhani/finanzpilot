"""Tests for category endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.categories.models import Category, TaxCategory


class TestCategoryEndpoints:
    """Test category CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_list_categories(
        self, client: AsyncClient, test_user_token: str
    ):
        """Test listing all categories (flat list)."""
        response = await client.get(
            "/api/categories",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have seed data

        # Check structure of first item
        first_cat = data[0]
        assert "id" in first_cat
        assert "name" in first_cat
        assert "name_de" in first_cat
        assert "is_income" in first_cat

    @pytest.mark.asyncio
    async def test_list_categories_tree(
        self, client: AsyncClient, test_user_token: str
    ):
        """Test listing categories as hierarchical tree."""
        response = await client.get(
            "/api/categories/tree",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Find a parent category with children
        parent_with_children = next(
            (cat for cat in data if cat.get("children")), None
        )
        assert parent_with_children is not None
        assert isinstance(parent_with_children["children"], list)
        assert len(parent_with_children["children"]) > 0

    @pytest.mark.asyncio
    async def test_get_category_by_id(
        self, client: AsyncClient, test_user_token: str, db: AsyncSession
    ):
        """Test getting a single category by ID."""
        # Get first category from DB
        result = await db.execute(select(Category.id).limit(1))
        category_id = result.scalar_one()

        response = await client.get(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(category_id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_category(
        self, client: AsyncClient, test_user_token: str
    ):
        """Test getting a category that doesn't exist."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/categories/{fake_uuid}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_category(
        self, client: AsyncClient, test_user_token: str
    ):
        """Test creating a new custom category."""
        new_category = {
            "name": "Custom Category",
            "name_de": "Benutzerdefiniert",
            "is_income": False,
            "icon": "Star",
            "color": "#FF5733",
            "sort_order": 100,
        }

        response = await client.post(
            "/api/categories",
            json=new_category,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == new_category["name"]
        assert data["name_de"] == new_category["name_de"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_subcategory(
        self, client: AsyncClient, test_user_token: str, db: AsyncSession
    ):
        """Test creating a subcategory under a parent."""
        # Get a parent category
        result = await db.execute(
            select(Category.id).where(Category.parent_id.is_(None)).limit(1)
        )
        parent_id = result.scalar_one()

        new_subcategory = {
            "name": "Custom Subcategory",
            "name_de": "Benutzerdefinierte Unterkategorie",
            "parent_id": str(parent_id),
            "is_income": False,
            "icon": "Tag",
            "color": "#33FF57",
            "sort_order": 10,
        }

        response = await client.post(
            "/api/categories",
            json=new_subcategory,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == new_subcategory["name"]
        assert data["parent_id"] == str(parent_id)

    @pytest.mark.asyncio
    async def test_create_category_invalid_color(
        self, client: AsyncClient, test_user_token: str
    ):
        """Test creating a category with invalid color format."""
        invalid_category = {
            "name": "Invalid Color",
            "name_de": "Ungültige Farbe",
            "is_income": False,
            "color": "not-a-hex-color",  # Invalid format
            "sort_order": 100,
        }

        response = await client.post(
            "/api/categories",
            json=invalid_category,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_category(
        self, client: AsyncClient, test_user_token: str, db: AsyncSession
    ):
        """Test updating an existing category."""
        # Get a category
        result = await db.execute(
            select(Category.id).where(Category.parent_id.is_(None)).limit(1)
        )
        category_id = result.scalar_one()

        update_data = {
            "name": "Updated Name",
            "color": "#ABCDEF",
        }

        response = await client.put(
            f"/api/categories/{category_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["color"] == update_data["color"]

    @pytest.mark.asyncio
    async def test_delete_category_without_children(
        self, client: AsyncClient, test_user_token: str, db: AsyncSession
    ):
        """Test deleting a category without children."""
        # Create a test category
        new_category = {
            "name": "To Delete",
            "name_de": "Zu Löschen",
            "is_income": False,
            "sort_order": 999,
        }

        create_response = await client.post(
            "/api/categories",
            json=new_category,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        category_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_category_with_children_fails(
        self, client: AsyncClient, test_user_token: str, db: AsyncSession
    ):
        """Test that deleting a parent category with children fails."""
        # Get a parent with children
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Category)
            .where(Category.parent_id.is_(None))
            .options(selectinload(Category.children))
        )
        parents = list(result.scalars().all())
        parent_with_children = next((p for p in parents if p.children), None)
        assert parent_with_children is not None
        parent_id = parent_with_children.id

        response = await client.delete(
            f"/api/categories/{parent_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 400  # Cannot delete parent with children

    @pytest.mark.asyncio
    async def test_categories_require_auth(self, client: AsyncClient):
        """Test that category endpoints require authentication."""
        response = await client.get("/api/categories")
        assert response.status_code in [401, 403]  # Either Unauthorized or Forbidden


class TestTaxCategoryEndpoints:
    """Test tax category endpoints."""

    @pytest.mark.asyncio
    async def test_list_tax_categories(
        self, client: AsyncClient, test_user_token: str
    ):
        """Test listing all tax categories."""
        response = await client.get(
            "/api/categories/tax",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have seed data

        # Check structure
        first_tax_cat = data[0]
        assert "id" in first_tax_cat
        assert "name" in first_tax_cat
        assert "name_de" in first_tax_cat
        assert "anlage" in first_tax_cat
        assert "deductible_percent" in first_tax_cat

    @pytest.mark.asyncio
    async def test_get_tax_category_by_id(
        self, client: AsyncClient, test_user_token: str, db: AsyncSession
    ):
        """Test getting a single tax category by ID."""
        result = await db.execute(select(TaxCategory.id).limit(1))
        tax_cat_id = result.scalar_one()

        response = await client.get(
            f"/api/categories/tax/{tax_cat_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(tax_cat_id)

    @pytest.mark.asyncio
    async def test_filter_tax_categories_by_anlage(
        self, client: AsyncClient, test_user_token: str
    ):
        """Test filtering tax categories by anlage (tax form)."""
        response = await client.get(
            "/api/categories/tax?anlage=N",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All results should have anlage = "N"
        for tax_cat in data:
            assert tax_cat["anlage"] == "N"

    @pytest.mark.asyncio
    async def test_tax_categories_require_auth(self, client: AsyncClient):
        """Test that tax category endpoints require authentication."""
        response = await client.get("/api/categories/tax")
        assert response.status_code in [401, 403]  # Either Unauthorized or Forbidden
