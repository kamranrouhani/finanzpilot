"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User


class TestRegister:
    """Test user registration."""

    async def test_register_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful user registration."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "testpass123"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data

        # Verify user was created in database
        result = await db_session.execute(
            select(User).where(User.username == "testuser")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.username == "testuser"

    async def test_register_duplicate_username(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test registration with duplicate username."""
        # Create first user
        await client.post(
            "/api/auth/register",
            json={"username": "duplicate", "password": "password123"},
        )

        # Try to create second user with same username
        response = await client.post(
            "/api/auth/register",
            json={"username": "duplicate", "password": "different123"},
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "short"},
        )

        assert response.status_code == 422  # Validation error

    async def test_register_short_username(self, client: AsyncClient):
        """Test registration with short username."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "ab", "password": "password123"},
        )

        assert response.status_code == 422  # Validation error

    async def test_register_invalid_username(self, client: AsyncClient):
        """Test registration with invalid username characters."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "test user!", "password": "password123"},
        )

        assert response.status_code == 422  # Validation error


class TestLogin:
    """Test user login."""

    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # First register a user
        await client.post(
            "/api/auth/register",
            json={"username": "logintest", "password": "testpass123"},
        )

        # Then login
        response = await client.post(
            "/api/auth/login",
            json={"username": "logintest", "password": "testpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login with wrong password."""
        # Register a user
        await client.post(
            "/api/auth/register",
            json={"username": "wrongpass", "password": "correctpass123"},
        )

        # Try to login with wrong password
        response = await client.post(
            "/api/auth/login",
            json={"username": "wrongpass", "password": "wrongpass123"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent username."""
        response = await client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()


class TestGetCurrentUser:
    """Test get current user endpoint."""

    async def test_get_me_success(self, client: AsyncClient):
        """Test getting current user with valid token."""
        # Register and login
        await client.post(
            "/api/auth/register",
            json={"username": "metest", "password": "testpass123"},
        )
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "metest", "password": "testpass123"},
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "metest"
        assert "id" in data
        assert "created_at" in data

    async def test_get_me_no_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/auth/me")

        assert response.status_code == 403  # Forbidden

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401
