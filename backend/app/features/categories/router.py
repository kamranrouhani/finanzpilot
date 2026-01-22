"""Category and TaxCategory API endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.shared.dependencies import get_current_user
from app.features.auth.models import User
from app.features.categories import service
from app.features.categories.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryTreeResponse,
    CategoryUpdate,
    TaxCategoryResponse,
)

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CategoryResponse]:
    """List all categories (flat list)."""
    categories = await service.get_all_categories(db)
    return categories


@router.get("/tree", response_model=List[CategoryTreeResponse])
async def list_categories_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CategoryTreeResponse]:
    """List categories as hierarchical tree structure."""
    tree = await service.get_category_tree(db)
    return tree


@router.get("/tax", response_model=List[TaxCategoryResponse])
async def list_tax_categories(
    anlage: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TaxCategoryResponse]:
    """List all tax categories, optionally filtered by anlage (tax form)."""
    tax_categories = await service.get_all_tax_categories(db, anlage=anlage)
    return tax_categories


@router.get("/tax/{tax_category_id}", response_model=TaxCategoryResponse)
async def get_tax_category(
    tax_category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaxCategoryResponse:
    """Get a single tax category by ID."""
    tax_category = await service.get_tax_category_by_id(db, tax_category_id)
    if not tax_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax category not found",
        )
    return tax_category


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """Get a single category by ID."""
    category = await service.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """Create a new category."""
    category = await service.create_category(db, category_data)
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """Update an existing category."""
    try:
        category = await service.update_category(db, category_id, category_data)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return category
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a category (only if it has no children or transactions)."""
    try:
        await service.delete_category(db, category_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except service.CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
