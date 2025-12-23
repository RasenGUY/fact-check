"""Shared test fixtures and configuration."""

import os
import pytest
from unittest.mock import AsyncMock

# Set test environment variables before importing app modules
os.environ["OPENROUTER_API_KEY"] = "test-key-for-testing"


@pytest.fixture
def anyio_backend():
    """Configure anyio to use asyncio."""
    return "asyncio"


@pytest.fixture
def mock_websearch_response():
    """Mock websearch results."""
    from app.adapters.openrouter_websearch_adapter import WebsearchResponse

    return [
        WebsearchResponse(
            title="NASA confirms sky is blue",
            url="https://nasa.gov/sky",
            content="The sky appears blue due to Rayleigh scattering of sunlight.",
        ),
        WebsearchResponse(
            title="Scientific American: Why is the sky blue?",
            url="https://scientificamerican.com/sky-blue",
            content="Blue light is scattered more than other colors because it travels in shorter waves.",
        ),
    ]


@pytest.fixture
def mock_claim_review():
    """Reusable mock ClaimReview for tests."""
    from app.models.response import ClaimReview, Rating, ItemReviewed

    return ClaimReview(
        claimReviewed="The sky is blue",
        datePublished="2025-01-01",
        reviewRating=Rating(ratingValue="5", alternateName="True"),
        url="https://fact-check.wordlift.io/review/sky-is-blue",
        reviewBody="Confirmed by NASA research on Rayleigh scattering.",
        itemReviewed=ItemReviewed(url=["https://nasa.gov/sky"]),
    )


@pytest.fixture
def mock_websearch_adapter(mock_websearch_response):
    """Mock OpenRouterWebsearchAdapter."""
    adapter = AsyncMock()
    adapter.search.return_value = mock_websearch_response
    return adapter


@pytest.fixture
def mock_openrouter_adapter(mock_claim_review):
    """Mock OpenRouterAdapter."""
    adapter = AsyncMock()
    adapter.make_request.return_value = mock_claim_review
    return adapter


@pytest.fixture
def mock_pipeline(mock_claim_review):
    """Mock FactCheckPipeline."""
    pipeline = AsyncMock()
    pipeline.execute.return_value = mock_claim_review
    return pipeline
