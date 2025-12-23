"""Integration tests for the full API flow."""

import pytest
import respx
from httpx import Response, ASGITransport, AsyncClient
import json

from app.main import app


# Mock responses for OpenRouter API
WEBSEARCH_RESPONSE = {
    "id": "chatcmpl-websearch-123",
    "object": "chat.completion",
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "results": [
                            {
                                "title": "NASA: The Sky Appears Blue",
                                "url": "https://nasa.gov/sky-blue",
                                "content": "The sky appears blue due to Rayleigh scattering of sunlight by the atmosphere.",
                            },
                            {
                                "title": "Scientific American: Why Blue?",
                                "url": "https://scientificamerican.com/blue-sky",
                                "content": "Blue light has a shorter wavelength and is scattered more than other colors.",
                            },
                        ]
                    }
                ),
            },
        }
    ],
}

EVALUATION_RESPONSE = {
    "id": "chatcmpl-eval-456",
    "object": "chat.completion",
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {
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
                            "worstRating": "1",
                        },
                        "url": "https://fact-check.wordlift.io/review/sky-is-blue",
                        "reviewBody": "This claim is verified as true. NASA confirms that the sky appears blue due to Rayleigh scattering.",
                        "itemReviewed": {
                            "@type": "CreativeWork",
                            "url": ["https://nasa.gov/sky-blue"],
                        },
                    }
                ),
                "parsed": {
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
                        "worstRating": "1",
                    },
                    "url": "https://fact-check.wordlift.io/review/sky-is-blue",
                    "reviewBody": "This claim is verified as true. NASA confirms that the sky appears blue due to Rayleigh scattering.",
                    "itemReviewed": {
                        "@type": "CreativeWork",
                        "url": ["https://nasa.gov/sky-blue"],
                    },
                },
            },
        }
    ],
}


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self):
        """Test health endpoint returns 200."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

            assert response.status_code == 200
            assert response.json()["status"] == "healthy"


class TestFactCheckEndpointValidation:
    """Tests for fact-check endpoint validation."""

    @pytest.mark.asyncio
    async def test_empty_query_returns_422(self):
        """Test that empty query returns validation error."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/fact-check", json={"query": ""})

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_query_returns_422(self):
        """Test that missing query returns validation error."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/fact-check", json={})

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_too_long_returns_422(self):
        """Test that query exceeding max length returns validation error."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/fact-check", json={"query": "x" * 1001})

            assert response.status_code == 422


class TestFactCheckEndpointIntegration:
    """Integration tests for fact-check endpoint with mocked OpenRouter."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_fact_check_full_flow(self, respx_mock):
        """Test full fact-check flow with mocked OpenRouter API."""
        # Track call count to return different responses
        call_count = {"count": 0}

        def mock_openrouter(request):
            call_count["count"] += 1
            if call_count["count"] == 1:
                # First call: websearch
                return Response(200, json=WEBSEARCH_RESPONSE)
            else:
                # Second call: evaluation
                return Response(200, json=EVALUATION_RESPONSE)

        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").mock(
            side_effect=mock_openrouter
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/fact-check", json={"query": "The sky is blue"}
            )

            # Should succeed
            assert response.status_code == 200

            # Verify response structure
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    @pytest.mark.asyncio
    @respx.mock
    async def test_fact_check_api_error_handled(self, respx_mock):
        """Test that API errors are handled gracefully."""
        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=Response(500, json={"error": "Internal server error"})
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/fact-check", json={"query": "Test claim"}
            )

            # Should return error response
            assert response.status_code == 500


class TestResponseTransformation:
    """Tests for response transformation middleware."""

    @pytest.mark.asyncio
    async def test_health_not_transformed(self):
        """Test that health endpoint is not transformed."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

            # Health should return raw response, not wrapped
            data = response.json()
            assert "status" in data
            assert "success" not in data  # Not transformed

    @pytest.mark.asyncio
    async def test_validation_error_transformed(self):
        """Test that validation errors are transformed."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/fact-check", json={"query": ""})

            data = response.json()
            assert data["success"] is False
            assert "error" in data
