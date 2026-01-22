"""Pytest configuration and fixtures."""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app

# Test database URL - configurable via environment, with fallback for local development
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://finanzpilot:localdevpassword123@postgres:5432/finanzpilot_test"
).replace("postgresql://", "postgresql+asyncpg://")

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create test database tables and seed data before tests."""
    from uuid import uuid4
    from sqlalchemy import text
    from app.shared.seed_data import SEED_CATEGORIES, SEED_TAX_CATEGORIES

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Insert seed data for tests
        # Tax categories
        for tax_cat in SEED_TAX_CATEGORIES:
            await conn.execute(
                text("""
                    INSERT INTO tax_categories (id, name, name_de, anlage, description, deductible_percent, created_at, updated_at)
                    VALUES (:id, :name, :name_de, :anlage, :description, :deductible_percent, now(), now())
                """),
                {
                    "id": str(uuid4()),
                    "name": tax_cat["name"],
                    "name_de": tax_cat["name_de"],
                    "anlage": tax_cat.get("anlage"),
                    "description": tax_cat.get("description"),
                    "deductible_percent": tax_cat["deductible_percent"],
                }
            )

        # Categories (parents first, then children)
        for cat in SEED_CATEGORIES:
            parent_id = str(uuid4())
            await conn.execute(
                text("""
                    INSERT INTO categories (id, name, name_de, parent_id, is_income, icon, color, sort_order, created_at, updated_at)
                    VALUES (:id, :name, :name_de, :parent_id, :is_income, :icon, :color, :sort_order, now(), now())
                """),
                {
                    "id": parent_id,
                    "name": cat["name"],
                    "name_de": cat["name_de"],
                    "parent_id": None,
                    "is_income": cat["is_income"],
                    "icon": cat["icon"],
                    "color": cat["color"],
                    "sort_order": cat["sort_order"],
                }
            )

            # Insert children if present
            for child in cat.get("children", []):
                await conn.execute(
                    text("""
                        INSERT INTO categories (id, name, name_de, parent_id, is_income, icon, color, sort_order, created_at, updated_at)
                        VALUES (:id, :name, :name_de, :parent_id, :is_income, :icon, :color, :sort_order, now(), now())
                    """),
                    {
                        "id": str(uuid4()),
                        "name": child["name"],
                        "name_de": child["name_de"],
                        "parent_id": parent_id,
                        "is_income": cat["is_income"],
                        "icon": child["icon"],
                        "color": cat["color"],
                        "sort_order": child["sort_order"],
                    }
                )

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def db(db_session: AsyncSession) -> AsyncSession:
    """Alias for db_session for easier test naming."""
    return db_session


@pytest.fixture
async def test_user(db_session: AsyncSession) -> dict:
    """Create a test user and return user data."""
    from sqlalchemy import select
    from app.features.auth.models import User
    from app.features.auth.service import hash_password

    # Check if user already exists
    result = await db_session.execute(
        select(User).where(User.username == "testuser")
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return {"id": existing_user.id, "username": existing_user.username}

    # Create new user if doesn't exist
    user = User(
        username="testuser",
        password_hash=hash_password("testpassword123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return {"id": user.id, "username": user.username}


@pytest.fixture
async def test_user_token(client: AsyncClient, test_user: dict) -> str:
    """Create a test user and return authentication token."""
    # Login to get token
    response = await client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpassword123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return token


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
