"""AI service for LLM-powered features."""
import logging
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


async def get_available_categories(db: AsyncSession) -> list[str]:
    """Get list of available category names.

    Args:
        db: Database session

    Returns:
        List of category names (parent categories only)
    """
    result = await db.execute(
        select(Category.name).where(Category.parent_id.is_(None))
    )
    categories = result.scalars().all()
    return list(categories)


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

        # Validate category exists
        suggested_category = result.get("category", "")
        if suggested_category not in categories:
            # Find closest match or default to first category
            suggested_category = categories[0] if categories else "Uncategorized"
            result["confidence"] = 0.1  # Low confidence for fallback

        return CategorySuggestion(
            category=suggested_category,
            confidence=min(max(float(result.get("confidence", 0.5)), 0.0), 1.0),
            reasoning=result.get("reasoning")
        )

    except Exception as e:
        logger.error(f"AI category suggestion failed: {str(e)}")
        # Return a safe fallback
        return CategorySuggestion(
            category=categories[0] if categories else "Uncategorized",
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
