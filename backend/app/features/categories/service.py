"""Business logic for categories."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.categories.models import Category, TaxCategory
from app.features.categories.schemas import CategoryCreate, CategoryUpdate


class CategoryNotFoundError(Exception):
    """Raised when a category is not found."""

    pass


async def get_all_categories(db: AsyncSession) -> List[Category]:
    """Get all categories as a flat list."""
    result = await db.execute(
        select(Category).order_by(Category.sort_order, Category.name)
    )
    return list(result.scalars().all())


async def get_category_tree(db: AsyncSession) -> List[dict]:
    """Get categories as a hierarchical tree (parents with children)."""
    # Get all parent categories (those without parent_id)
    result = await db.execute(
        select(Category)
        .where(Category.parent_id.is_(None))
        .options(selectinload(Category.children))
        .order_by(Category.sort_order, Category.name)
    )
    parents = list(result.scalars().all())

    # Convert to dict to avoid lazy-loading issues with Pydantic
    tree = []
    for parent in parents:
        parent_dict = {
            "id": parent.id,
            "name": parent.name,
            "name_de": parent.name_de,
            "parent_id": parent.parent_id,
            "is_income": parent.is_income,
            "icon": parent.icon,
            "color": parent.color,
            "sort_order": parent.sort_order,
            "created_at": parent.created_at,
            "updated_at": parent.updated_at,
            "children": [
                {
                    "id": child.id,
                    "name": child.name,
                    "name_de": child.name_de,
                    "parent_id": child.parent_id,
                    "is_income": child.is_income,
                    "icon": child.icon,
                    "color": child.color,
                    "sort_order": child.sort_order,
                    "created_at": child.created_at,
                    "updated_at": child.updated_at,
                    "children": [],  # Leaf nodes have no children
                }
                for child in sorted(parent.children, key=lambda c: (c.sort_order, c.name))
            ],
        }
        tree.append(parent_dict)

    return tree


async def get_category_by_id(db: AsyncSession, category_id: UUID) -> Optional[Category]:
    """Get a single category by ID."""
    result = await db.execute(
        select(Category)
        .where(Category.id == category_id)
        .options(selectinload(Category.children))
    )
    return result.scalar_one_or_none()


async def create_category(db: AsyncSession, data: CategoryCreate) -> Category:
    """Create a new category."""
    category = Category(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def _get_descendant_ids(db: AsyncSession, category_id: UUID) -> set[UUID]:
    """Get all descendant category IDs recursively."""
    # Use a recursive CTE to get all descendants
    from sqlalchemy import text

    query = text("""
        WITH RECURSIVE descendants AS (
            SELECT id FROM categories WHERE parent_id = :category_id
            UNION ALL
            SELECT c.id FROM categories c
            INNER JOIN descendants d ON c.parent_id = d.id
        )
        SELECT id FROM descendants
    """)

    result = await db.execute(query, {"category_id": category_id})
    return {row[0] for row in result.fetchall()}


async def update_category(
    db: AsyncSession, category_id: UUID, data: CategoryUpdate
) -> Optional[Category]:
    """Update an existing category."""
    category = await get_category_by_id(db, category_id)
    if not category:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # Validate parent_id to prevent circular references and self-references
    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]

        # Prevent self-reference
        if new_parent_id == category_id:
            raise ValueError("Category cannot be its own parent")

        # Prevent circular reference (new parent is a descendant)
        if new_parent_id is not None:
            descendant_ids = await _get_descendant_ids(db, category_id)
            if new_parent_id in descendant_ids:
                raise ValueError("Cannot set parent to a descendant category (would create circular reference)")

    # Update only provided fields
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(db: AsyncSession, category_id: UUID) -> None:
    """Delete a category if it has no children or transactions.

    Raises:
        CategoryNotFoundError: If category doesn't exist
        ValueError: If category has children or transactions
    """
    category = await get_category_by_id(db, category_id)
    if not category:
        raise CategoryNotFoundError(f"Category {category_id} not found")

    # Check if has children (exclude self-referential categories)
    actual_children = [child for child in category.children if child.id != category_id]
    if actual_children:
        raise ValueError("Cannot delete category with children")

    # Check if has transactions (import here to avoid circular dependency)
    from app.features.transactions.models import Transaction

    transaction_count_query = select(func.count()).select_from(Transaction).where(
        or_(
            Transaction.category_id == category_id,
            Transaction.subcategory_id == category_id
        )
    )
    result = await db.execute(transaction_count_query)
    transaction_count = result.scalar()

    if transaction_count > 0:
        raise ValueError(f"Cannot delete category with {transaction_count} associated transaction(s)")

    await db.delete(category)
    await db.commit()


async def get_all_tax_categories(
    db: AsyncSession, anlage: Optional[str] = None
) -> List[TaxCategory]:
    """Get all tax categories, optionally filtered by anlage (tax form)."""
    query = select(TaxCategory).order_by(TaxCategory.name)

    if anlage:
        query = query.where(TaxCategory.anlage == anlage)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_tax_category_by_id(
    db: AsyncSession, tax_category_id: UUID
) -> Optional[TaxCategory]:
    """Get a single tax category by ID."""
    result = await db.execute(
        select(TaxCategory).where(TaxCategory.id == tax_category_id)
    )
    return result.scalar_one_or_none()
