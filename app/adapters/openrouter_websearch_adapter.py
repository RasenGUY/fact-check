from typing import Any, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config.settings import settings
from app.config.model_config import ModelSelector, ModelUseCase
from app.utils.logging import get_logger
from app.utils.retry_decorator import retry_with_exponential_backoff_async

logger = get_logger(__name__)


class WebsearchResponse(BaseModel):
    """Single search result from OpenRouter :online websearch."""

    title: str
    url: str
    content: str


class WebsearchResponseList(BaseModel):
    """Collection of websearch results."""

    results: list[WebsearchResponse]


class WebsearchException(Exception):
    """Raised when websearch fails."""

    pass


WEBSEARCH_SYSTEM_PROMPT = """You are a research assistant. Search the web for information
about the given claim and return structured results.

Return your findings as a JSON object with this structure:
{
    "results": [
        {
            "title": "Source title/headline",
            "url": "https://source-url.com",
            "content": "Relevant excerpt or summary from the source"
        }
    ]
}

Include 3-5 relevant sources. Focus on authoritative sources like news sites,
official organizations, and fact-checking websites."""


class OpenRouterWebsearchAdapter:
    """
    Web search adapter using OpenRouter's :online suffix.

    Pattern from seo-acg: Append ':online' to model name to enable
    built-in web search capability. No separate search API needed.

    Example: "x-ai/grok-4-fast" becomes "x-ai/grok-4-fast:online"
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.openrouter_api_url,
            api_key=settings.openrouter_api_key,
        )
        self.logger = get_logger(self.__class__.__name__)

    @retry_with_exponential_backoff_async(
        max_retries=3,
        base_delay=1.0,
        exceptions_to_retry=(Exception, WebsearchException),
    )
    async def search(
        self,
        *,
        query: str,
        max_results: int = 5,
    ) -> list[WebsearchResponse]:
        """
        Search for evidence using OpenRouter's :online websearch.

        Args:
            query: The claim to search for evidence about
            max_results: Maximum number of results (hint to LLM)

        Returns:
            List of WebsearchResponse objects with title, url, content
        """
        # Get websearch model (appends :online suffix)
        model = ModelSelector.get_websearch_model(ModelUseCase.FACT_CHECK_WEBSEARCH)

        messages = [
            {"role": "system", "content": WEBSEARCH_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Search for evidence about this claim: {query}\n\nReturn up to {max_results} relevant sources.",
            },
        ]

        self.logger.info("Performing websearch", query=query[:50], model=model)

        response = await self.client.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=WebsearchResponseList,
        )

        if not response.choices[0].message.parsed:
            raise WebsearchException("No response from websearch")

        result = response.choices[0].message.parsed

        self.logger.info(
            "Websearch complete", num_results=len(result.results), query=query[:50]
        )

        return result.results


# Singleton instance
openrouter_websearch_adapter = OpenRouterWebsearchAdapter()
