"""AI service for LLM-powered features."""
import logging
from functools import lru_cache
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai.ollama_client import ollama_client
from app.features.ai.prompts import CATEGORY_SUGGESTION_PROMPT
from app.features.ai.schemas import CategorySuggestion
from app.features.categories.models import Category
from app.features.transactions.models import Transaction

logger = logging.getLogger(__name__)

# Simple cache for category list (TTL handled by server restart)
_category_cache: Optional[list[str]] = None


async def get_available_categories(db: AsyncSession, use_cache: bool = True) -> list[str]:
    """Get list of available category names.

    Args:
        db: Database session
        use_cache: Whether to use cached categories (default True)

    Returns:
        List of category names (parent categories only)
    """
    global _category_cache

    # Use cache if available and requested
    if use_cache and _category_cache is not None:
        return _category_cache

    # Fetch from database
    result = await db.execute(
        select(Category.name).where(Category.parent_id.is_(None))
    )
    categories = list(result.scalars().all())

    # Update cache
    _category_cache = categories

    return categories


def _find_best_matching_category(suggested: str, available: list[str]) -> str:
    """Find best matching category using fuzzy matching.

    Args:
        suggested: AI-suggested category name
        available: List of available categories

    Returns:
        Best matching category name
    """
    if not available:
        return "Uncategorized"

    suggested_lower = suggested.lower()

    # Exact match (case-insensitive)
    for cat in available:
        if cat.lower() == suggested_lower:
            return cat

    # Substring match
    for cat in available:
        if suggested_lower in cat.lower() or cat.lower() in suggested_lower:
            return cat

    # Word matching (for compound categories)
    suggested_words = set(suggested_lower.split())
    best_match = None
    best_score = 0

    for cat in available:
        cat_words = set(cat.lower().split())
        common_words = suggested_words & cat_words
        if len(common_words) > best_score:
            best_score = len(common_words)
            best_match = cat

    if best_match and best_score > 0:
        return best_match

    # Default to first category as last resort
    return available[0]


async def suggest_category_for_transaction(
    db: AsyncSession,
    counterparty: Optional[str],
    description: Optional[str],
    amount: float
) -> CategorySuggestion:
    """Suggest a category for a transaction using AI.

    Args:
        db: Database session
        counterparty: Transaction counterparty
        description: Transaction description
        amount: Transaction amount

    Returns:
        CategorySuggestion with category name and confidence

    Raises:
        ValueError: If AI request fails or response is invalid
    """
    # Get available categories
    categories = await get_available_categories(db)
    categories_str = ", ".join(categories)

    # Build prompt
    prompt = CATEGORY_SUGGESTION_PROMPT.format(
        counterparty=counterparty or "Unknown",
        description=description or "No description",
        amount=amount,
        categories=categories_str
    )

    try:
        # Call Ollama
        response = await ollama_client.generate(
            model="qwen2.5:7b",
            prompt=prompt,
            temperature=0.1,
            format="json"
        )

        # Extract and validate JSON
        result = ollama_client.extract_json_from_response(response)

        # Validate and match category
        suggested_category = result.get("category", "")
        confidence = min(max(float(result.get("confidence", 0.5)), 0.0), 1.0)

        if suggested_category not in categories:
            # Use fuzzy matching to find best category
            suggested_category = _find_best_matching_category(suggested_category, categories)
            # Reduce confidence if we had to fuzzy match
            confidence *= 0.7

        return CategorySuggestion(
            category=suggested_category,
            confidence=confidence,
            reasoning=result.get("reasoning")
        )

    except Exception as e:
        logger.error(f"AI category suggestion failed: {str(e)}")
        # Return a safe fallback - prefer income/expense based category if possible
        fallback_category = categories[0] if categories else "Uncategorized"
        if amount < 0 and any('expense' in c.lower() for c in categories):
            fallback_category = next(c for c in categories if 'expense' in c.lower())
        elif amount > 0 and any('income' in c.lower() for c in categories):
            fallback_category = next(c for c in categories if 'income' in c.lower())

        return CategorySuggestion(
            category=fallback_category,
            confidence=0.1,
            reasoning=f"AI error: {str(e)[:100]}"
        )


async def bulk_categorize_transactions(
    db: AsyncSession,
    user_id: UUID,
    transaction_ids: list[UUID]
) -> dict:
    """Categorize multiple transactions in bulk.

    Args:
        db: Database session
        user_id: User ID
        transaction_ids: List of transaction IDs to categorize

    Returns:
        Dict with results, successful count, and failed count
    """
    results = []
    successful = 0
    failed = 0

    for txn_id in transaction_ids:
        try:
            # Get transaction
            result = await db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.id == txn_id,
                        Transaction.user_id == user_id
                    )
                )
            )
            transaction = result.scalar_one_or_none()

            if not transaction:
                results.append({
                    "transaction_id": str(txn_id),
                    "suggested_category": None,
                    "confidence": 0.0,
                    "error": "Transaction not found"
                })
                failed += 1
                continue

            # Get AI suggestion
            suggestion = await suggest_category_for_transaction(
                db,
                transaction.counterparty,
                transaction.description,
                float(transaction.amount)
            )

            results.append({
                "transaction_id": str(txn_id),
                "suggested_category": suggestion.category,
                "confidence": suggestion.confidence,
                "error": None
            })
            successful += 1

        except Exception as e:
            logger.error(f"Failed to categorize transaction {txn_id}: {str(e)}")
            results.append({
                "transaction_id": str(txn_id),
                "suggested_category": None,
                "confidence": 0.0,
                "error": str(e)[:100]
            })
            failed += 1

    return {
        "results": results,
        "total": len(transaction_ids),
        "successful": successful,
        "failed": failed
    }
