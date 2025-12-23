import asyncio
import functools
import random
from typing import Type, Union

from app.utils.logging import get_logger

logger = get_logger(__name__)


def retry_with_exponential_backoff_async(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_factor: float = 0.1,
    exceptions_to_retry: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
):
    """
    Decorator for retrying an async function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        jitter_factor: Randomness factor (0-1) to add to delay
        exceptions_to_retry: Exception types to retry on

    Returns:
        Decorated function with retry logic
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0

            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions_to_retry as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(
                            f"Failed after {max_retries} retries: {func.__name__} - {str(e)}"
                        )
                        raise

                    # Calculate backoff delay with jitter
                    delay = min(max_delay, base_delay * (2 ** (retries - 1)))
                    jitter = random.uniform(0, jitter_factor * delay)
                    wait_time = delay + jitter

                    logger.warning(
                        f"Error in {func.__name__} (attempt {retries}/{max_retries}): {str(e)}. "
                        f"Retrying in {wait_time:.2f} seconds..."
                    )
                    await asyncio.sleep(wait_time)

        return wrapper

    return decorator
