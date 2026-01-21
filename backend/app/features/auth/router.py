"""Authentication routes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.features.auth.models import User
from app.features.auth.schemas import (Token, UserCreate, UserLogin,
                                       UserResponse)
from app.features.auth.service import login_user, register_user
from app.shared.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        User: Created user
    """
    return await register_user(db, user_data)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Login with username and password.

    Args:
        credentials: Login credentials
        db: Database session

    Returns:
        Token: JWT access token
    """
    return await login_user(db, credentials.username, credentials.password)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current authenticated user.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current user data
    """
    return current_user
