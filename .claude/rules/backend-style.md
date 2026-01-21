---
paths:
  - "backend/**/*.py"
---

# Python/FastAPI Code Style

## Formatting
- Use Black for formatting (line length 88)
- Use isort for imports
- Use ruff for linting

## Type Hints
Always use type hints:
```python
def get_user(user_id: UUID) -> User | None:
    pass

async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession
) -> Transaction:
    pass
```

## Async/Await
- All database operations must be async
- Use `async def` for route handlers
- Use `AsyncSession` from SQLAlchemy

## Pydantic Schemas
```python
from pydantic import BaseModel, Field
from datetime import date
from uuid import UUID

class TransactionCreate(BaseModel):
    date: date
    amount: float = Field(..., description="Amount in EUR")
    counterparty: str = Field(..., min_length=1, max_length=255)
    
    model_config = ConfigDict(from_attributes=True)
```

## SQLAlchemy Models
```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## Error Handling
```python
from fastapi import HTTPException, status

# Use specific HTTP exceptions
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Transaction not found"
)

# Or custom exceptions with handler
class TransactionNotFoundError(Exception):
    pass
```

## Dependency Injection
```python
from fastapi import Depends
from app.shared.dependencies import get_db, get_current_user

@router.get("/transactions")
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pass
```

## Logging
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing transaction", extra={"transaction_id": str(tx.id)})
logger.error("Ollama connection failed", exc_info=True)
```

## Feature Structure
```
features/
└── transactions/
    ├── __init__.py
    ├── router.py      # FastAPI routes
    ├── service.py     # Business logic
    ├── schemas.py     # Pydantic models
    └── models.py      # SQLAlchemy models
```
