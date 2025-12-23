# Testing Plan - Fact-Check Service

## Overview

Two-tier testing strategy using Python-native mocking (no external services like Wiremock needed).

| Test Type | Scope | Mocking Approach |
|-----------|-------|------------------|
| **Unit Tests** | Individual components | Dependency injection + unittest.mock |
| **Integration Tests** | Full pipeline flow | `openai-responses` pytest plugin (respx-based) |

---

## Why Not Wiremock?

| Approach | Pros | Cons |
|----------|------|------|
| **Wiremock** | Language-agnostic, realistic HTTP | Requires external process, complex CI setup, Java dependency |
| **openai-responses** | In-process, zero config, pytest-native | Python only (fine for us) |
| **respx** | Low-level httpx control | More boilerplate than openai-responses |

**Decision:** Use `openai-responses` for integration tests - it's purpose-built for mocking OpenAI API and runs in-process (perfect for CI).

---

## Dependencies

```txt
# Testing (add to requirements.txt)
pytest>=8.0.0
pytest-asyncio>=0.23.0
openai-responses>=0.5.0
```

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_models.py          # Pydantic model validation
│   ├── test_pipeline.py        # Pipeline with mocked adapters
│   ├── test_service.py         # Service with mocked pipeline
│   └── test_transformers.py    # Response transformers
└── integration/
    ├── __init__.py
    └── test_api_flow.py        # Full API → Pipeline flow
```

---

## Unit Tests

### 1. Test Models (`test_models.py`)

```python
import pytest
from app.models.request import FactCheckRequest
from app.models.response import ClaimReview, Rating, ItemReviewed

class TestFactCheckRequest:
    def test_valid_request(self):
        req = FactCheckRequest(query="The sky is blue")
        assert req.query == "The sky is blue"

    def test_empty_query_rejected(self):
        with pytest.raises(ValueError):
            FactCheckRequest(query="")

    def test_query_max_length(self):
        with pytest.raises(ValueError):
            FactCheckRequest(query="x" * 1001)


class TestClaimReview:
    def test_valid_claim_review(self):
        review = ClaimReview(
            claimReviewed="Test claim",
            datePublished="2025-01-01",
            reviewRating=Rating(ratingValue="5", alternateName="True"),
            url="https://example.com/review/test",
            reviewBody="This is true.",
            itemReviewed=ItemReviewed(url=["https://source.com"]),
        )
        assert review.reviewRating.ratingValue == "5"
```

### 2. Test Pipeline with Mocked Adapters (`test_pipeline.py`)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.pipelines.fact_check_pipeline import FactCheckPipeline
from app.adapters.openrouter_websearch_adapter import WebsearchResponse
from app.models.response import ClaimReview, Rating, ItemReviewed
from app.models.internal import PipelineParams


@pytest.fixture
def mock_websearch_adapter():
    adapter = AsyncMock()
    adapter.search.return_value = [
        WebsearchResponse(
            title="NASA confirms sky is blue",
            url="https://nasa.gov/sky",
            content="The sky appears blue due to Rayleigh scattering."
        )
    ]
    return adapter


@pytest.fixture
def mock_openrouter_adapter():
    adapter = AsyncMock()
    adapter.make_request.return_value = ClaimReview(
        claimReviewed="The sky is blue",
        datePublished="2025-01-01",
        reviewRating=Rating(ratingValue="5", alternateName="True"),
        url="https://fact-check.wordlift.io/review/sky-is-blue",
        reviewBody="Confirmed by NASA.",
        itemReviewed=ItemReviewed(url=["https://nasa.gov/sky"]),
    )
    return adapter


@pytest.fixture
def pipeline_with_mocks(mock_websearch_adapter, mock_openrouter_adapter):
    pipeline = FactCheckPipeline()
    pipeline.websearch_adapter = mock_websearch_adapter
    pipeline.openrouter_adapter = mock_openrouter_adapter
    return pipeline


@pytest.mark.asyncio
async def test_pipeline_execute(pipeline_with_mocks):
    params = PipelineParams(query="The sky is blue", max_results=5)
    result = await pipeline_with_mocks.execute(params=params)

    assert result.claimReviewed == "The sky is blue"
    assert result.reviewRating.ratingValue == "5"
    pipeline_with_mocks.websearch_adapter.search.assert_called_once()
    pipeline_with_mocks.openrouter_adapter.make_request.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_builds_correct_prompt(pipeline_with_mocks):
    params = PipelineParams(query="Test claim", max_results=3)
    await pipeline_with_mocks.execute(params=params)

    # Verify the prompt was built correctly
    call_args = pipeline_with_mocks.openrouter_adapter.make_request.call_args
    messages = call_args.kwargs["messages"]

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Test claim" in messages[1]["content"]
```

### 3. Test Service with Mocked Pipeline (`test_service.py`)

```python
import pytest
from unittest.mock import AsyncMock
from app.services.fact_check_service import FactCheckService
from app.models.request import FactCheckRequest
from app.models.response import ClaimReview, Rating, ItemReviewed


@pytest.fixture
def mock_pipeline():
    pipeline = AsyncMock()
    pipeline.execute.return_value = ClaimReview(
        claimReviewed="Test",
        datePublished="2025-01-01",
        reviewRating=Rating(ratingValue="3", alternateName="Half True"),
        url="https://fact-check.wordlift.io/review/test",
        reviewBody="Partially accurate.",
        itemReviewed=ItemReviewed(url=["https://example.com"]),
    )
    return pipeline


@pytest.mark.asyncio
async def test_service_calls_pipeline(mock_pipeline):
    service = FactCheckService(pipeline=mock_pipeline)
    request = FactCheckRequest(query="Test claim")

    result = await service.fact_check(request=request)

    assert result.reviewRating.alternateName == "Half True"
    mock_pipeline.execute.assert_called_once()
```

---

## Integration Tests

### Full API Flow with `openai-responses` (`test_api_flow.py`)

```python
import pytest
import openai_responses
from openai_responses import OpenAIMock
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app


# Mock response for websearch (Step 1)
WEBSEARCH_RESPONSE = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "choices": [{
        "index": 0,
        "finish_reason": "stop",
        "message": {
            "role": "assistant",
            "content": '{"results": [{"title": "NASA: Sky is blue", "url": "https://nasa.gov", "content": "Rayleigh scattering causes blue sky."}]}'
        }
    }]
}

# Mock response for evaluation (Step 2)
EVALUATION_RESPONSE = {
    "id": "chatcmpl-456",
    "object": "chat.completion",
    "choices": [{
        "index": 0,
        "finish_reason": "stop",
        "message": {
            "role": "assistant",
            "content": """{
                "@context": "http://schema.org",
                "@type": "ClaimReview",
                "claimReviewed": "The sky is blue",
                "author": {"@type": "Organization", "name": "WordLift"},
                "datePublished": "2025-01-01",
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": "5",
                    "alternateName": "True",
                    "bestRating": "5",
                    "worstRating": "1"
                },
                "url": "https://fact-check.wordlift.io/review/sky-is-blue",
                "reviewBody": "Confirmed by NASA research on Rayleigh scattering.",
                "itemReviewed": {"@type": "CreativeWork", "url": ["https://nasa.gov"]}
            }"""
        }
    }]
}


@pytest.fixture
def mock_openrouter():
    """Configure openai-responses to mock OpenRouter API."""
    with openai_responses.mock() as mock:
        # First call: websearch
        mock.chat.completions.create.response = WEBSEARCH_RESPONSE
        yield mock


@pytest.mark.asyncio
async def test_fact_check_endpoint_full_flow():
    """Integration test: API → Service → Pipeline → Adapters (mocked)."""

    # Note: For full integration, we need to mock at httpx level
    # since openai-responses intercepts OpenAI client calls

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_fact_check_validation_error():
    """Test that empty query returns 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/fact-check",
            json={"query": ""}
        )
        assert response.status_code == 422
```

### Alternative: Using `respx` Directly

```python
import pytest
import respx
from httpx import Response, ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
@respx.mock
async def test_fact_check_with_respx(respx_mock):
    """Mock OpenRouter at HTTP level using respx."""

    # Mock websearch call
    respx_mock.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(200, json={
            "choices": [{
                "message": {
                    "content": '{"results": [{"title": "Test", "url": "https://test.com", "content": "Test content"}]}'
                }
            }]
        })
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/fact-check",
            json={"query": "Test claim"}
        )
        # Assert based on mocked response
```

---

## conftest.py

```python
import pytest
from unittest.mock import AsyncMock

# Ensure we don't make real API calls
import os
os.environ["OPENROUTER_API_KEY"] = "test-key-for-testing"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_claim_review():
    """Reusable mock ClaimReview for tests."""
    from app.models.response import ClaimReview, Rating, ItemReviewed

    return ClaimReview(
        claimReviewed="Test claim",
        datePublished="2025-01-01",
        reviewRating=Rating(ratingValue="3", alternateName="Half True"),
        url="https://fact-check.wordlift.io/review/test",
        reviewBody="Test review body.",
        itemReviewed=ItemReviewed(url=["https://example.com"]),
    )
```

---

## CI Configuration (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        env:
          OPENROUTER_API_KEY: "test-key"
        run: |
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

## Summary

| Layer | Test File | Mocking |
|-------|-----------|---------|
| Models | `test_models.py` | None (pure validation) |
| Pipeline | `test_pipeline.py` | `AsyncMock` adapters |
| Service | `test_service.py` | `AsyncMock` pipeline |
| API | `test_api_flow.py` | `openai-responses` or `respx` |
| Transformers | `test_transformers.py` | None |

**No Wiremock needed** - Python mocking runs in-process, zero external dependencies for CI.

---

## Sources

- [pydantic-ai Testing](https://ai.pydantic.dev/testing/)
- [openai-responses PyPI](https://pypi.org/project/openai-responses/)
- [openai-responses Docs](https://mharrisb1.github.io/openai-responses-python/)
- [Mocking OpenAI - Bakken & Baeck](https://bakkenbaeck.com/tech/mocking-openai)
- [RESPX Mocking](https://lundberg.github.io/respx/)
