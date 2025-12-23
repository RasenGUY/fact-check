from typing import Any, Optional, Type, TypeVar, Union

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config.settings import settings
from app.utils.logging import get_logger
from app.utils.retry_decorator import retry_with_exponential_backoff_async

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

EMPTY_RESPONSE_MESSAGE = "Response empty"


class OpenRouterAdapterException(Exception):
    """Raised when OpenRouterAdapter fails."""

    pass


class OpenRouterAdapter:
    """
    Unified adapter for all LLM calls via OpenRouter.

    Pattern from seo-acg: Single adapter with retry logic
    and structured output support.
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.openrouter_api_url,
            api_key=settings.openrouter_api_key,
            max_retries=3,
        )

    @retry_with_exponential_backoff_async(
        max_retries=3,
        base_delay=1.0,
        exceptions_to_retry=(Exception, OpenRouterAdapterException),
    )
    async def make_request(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        output_type: Optional[Type[T]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Union[T, str]:
        """
        Make LLM request with optional structured output.

        Args:
            model: Model identifier (e.g., "openai/gpt-4o-mini")
            messages: Chat messages array
            output_type: Pydantic model for structured output
            max_tokens: Optional token limit
            temperature: Optional temperature setting

        Returns:
            Parsed Pydantic model if output_type provided, else string
        """
        if output_type:
            # Use parse method for structured output
            response = await self.client.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=output_type,
                max_completion_tokens=max_tokens,
            )

            if not response.choices[0].message.parsed:
                raise OpenRouterAdapterException(EMPTY_RESPONSE_MESSAGE)

            return response.choices[0].message.parsed

        # Regular completion without structured output
        kwargs = {
            "model": model,
            "messages": messages,
        }

        if max_tokens:
            kwargs["max_completion_tokens"] = max_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature

        response = await self.client.chat.completions.create(**kwargs)

        if not response.choices[0].message.content:
            raise OpenRouterAdapterException(EMPTY_RESPONSE_MESSAGE)

        return response.choices[0].message.content


# Singleton instance
openrouter_adapter = OpenRouterAdapter()
