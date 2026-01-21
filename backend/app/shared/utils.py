"""Shared utility functions."""
import re


def transform_database_url(database_url: str) -> str:
    """
    Transform database URL to use asyncpg driver.

    Handles both 'postgresql://' and 'postgres://' schemes.

    Args:
        database_url: Original database URL

    Returns:
        str: Transformed URL with asyncpg driver
    """
    # Replace both postgresql:// and postgres:// with postgresql+asyncpg://
    return re.sub(r"^(postgres|postgresql)://", "postgresql+asyncpg://", database_url)
