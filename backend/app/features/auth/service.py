"""Authentication service."""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.features.auth.models import User
from app.features.auth.schemas import Token, UserCreate

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User ID to encode in token

    Returns:
        str: Encoded JWT token
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Register a new user.

    Args:
        db: Database session
        user_data: User registration data

    Returns:
        User: Created user

    Raises:
        HTTPException: If username already exists
    """
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create new user
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    """
    Authenticate a user.

    Args:
        db: Database session
        username: Username
        password: Plain password

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: If credentials are invalid
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def login_user(db: AsyncSession, username: str, password: str) -> Token:
    """
    Login a user and return JWT token.

    Args:
        db: Database session
        username: Username
        password: Plain password

    Returns:
        Token: JWT token response
    """
    user = await authenticate_user(db, username, password)
    access_token = create_access_token(str(user.id))

    return Token(access_token=access_token)
