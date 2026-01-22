"""AI prompts for various features."""

CATEGORY_SUGGESTION_PROMPT = """Based on this transaction, suggest the most appropriate category:

Transaction details:
- Counterparty: {counterparty}
- Description: {description}
- Amount: {amount} EUR

Available categories: {categories}

Respond with ONLY valid JSON (no explanations):
{{
  "category": "category_name",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}

Consider:
- Counterparty name (e.g., REWE = Groceries, Deutsche Bahn = Transport)
- Description keywords
- Amount range (e.g., large amounts might be rent, small amounts might be food)
"""

SPENDING_INSIGHTS_PROMPT = """Analyze this spending data and provide insights:

Monthly spending summary:
{spending_summary}

Top categories:
{top_categories}

Recent unusual transactions:
{unusual_transactions}

Respond with ONLY valid JSON:
{{
  "insights": [
    {{
      "type": "increase|decrease|anomaly|pattern",
      "category": "category_name",
      "message": "user-friendly message",
      "severity": "info|warning|critical"
    }}
  ],
  "recommendations": [
    "actionable recommendation"
  ]
}}

Focus on:
- Month-over-month changes
- Unusual spending patterns
- Budget optimization opportunities
"""

NATURAL_LANGUAGE_QUERY_PROMPT = """You are a financial assistant. Answer this question based on the user's transaction data:

Question: {question}

Available data:
{context}

Provide a clear, concise answer in {language}. If calculations are needed, show your work.
If the data doesn't support an answer, say so clearly.
"""
