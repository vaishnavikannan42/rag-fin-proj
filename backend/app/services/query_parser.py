"""Query parser service for extracting entities from natural language queries."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import List, Optional, Tuple

from ..dependencies import get_openai_client
from ..openai_client import OpenAIClient


EXTRACTION_PROMPT = """You are an entity extraction assistant for a financial RAG system.
Extract stock ticker symbols and time periods from the user's question.

Rules:
1. Tickers: Extract company stock symbols (e.g., AMZN, AAPL, GOOGL, MSFT). 
   - If a company name is mentioned (e.g., "Amazon"), convert to ticker (AMZN).
   - Return as uppercase list, or null if no company is mentioned.

2. Period: Extract fiscal quarter and year in format "Q#-YYYY" (e.g., "Q3-2025").
   - "last quarter" or "most recent quarter" -> use CURRENT_QUARTER
   - "Q3 2025" or "third quarter 2025" -> "Q3-2025"
   - Return null if no period is mentioned.

3. needs_clarification: Set to true if:
   - Multiple companies could be inferred but unclear which one
   - Time period is ambiguous (e.g., "recently" without specifics)
   - The question is too vague to determine what data is needed

4. clarification_message: If needs_clarification is true, provide a helpful message
   asking the user to specify what's missing.

Current date for reference: CURRENT_DATE

Respond ONLY with valid JSON in this exact format:
{
  "tickers": ["AMZN"] or null,
  "period": "Q3-2025" or null,
  "needs_clarification": false,
  "clarification_message": null or "Please specify..."
}"""


def _get_current_quarter() -> str:
    """Get the current fiscal quarter in Q#-YYYY format."""
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    return f"Q{quarter}-{now.year}"


def _resolve_relative_period(period: Optional[str]) -> Optional[str]:
    """Resolve relative period references like 'last quarter'."""
    if period == "CURRENT_QUARTER":
        return _get_current_quarter()
    return period


class QueryParser:
    """Parses user queries to extract ticker symbols and time periods."""

    def __init__(self, openai_client: Optional[OpenAIClient] = None) -> None:
        self._openai = openai_client or get_openai_client()

    def parse(self, question: str) -> Tuple[Optional[List[str]], Optional[str], bool, Optional[str]]:
        """
        Parse a question to extract entities.

        Returns:
            Tuple of (tickers, period, needs_clarification, clarification_message)
        """
        current_date = datetime.now().strftime("%B %d, %Y")
        current_quarter = _get_current_quarter()

        prompt = EXTRACTION_PROMPT.replace("CURRENT_DATE", current_date).replace(
            "CURRENT_QUARTER", current_quarter
        )

        try:
            response = self._openai.chat(system_prompt=prompt, user_message=question)
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            data = json.loads(response)

            tickers = data.get("tickers")
            period = data.get("period")
            needs_clarification = data.get("needs_clarification", False)
            clarification_message = data.get("clarification_message")

            # Normalize tickers to uppercase
            if tickers:
                tickers = [t.upper() for t in tickers]

            # Resolve relative periods
            period = _resolve_relative_period(period)

            return tickers, period, needs_clarification, clarification_message

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # If parsing fails, return needs_clarification
            return (
                None,
                None,
                True,
                "I couldn't understand your query. Please specify the company ticker and time period.",
            )


def get_query_parser() -> QueryParser:
    """Factory function to create a QueryParser instance."""
    return QueryParser(openai_client=get_openai_client())

