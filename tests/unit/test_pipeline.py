"""Unit tests for FactCheckPipeline."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.pipelines.fact_check_pipeline import FactCheckPipeline
from app.adapters.openrouter_websearch_adapter import WebsearchResponse
from app.models.response import ClaimReview, Rating, ItemReviewed
from app.models.internal import PipelineParams


class TestFactCheckPipeline:
    """Tests for FactCheckPipeline."""

    @pytest.fixture
    def pipeline_with_mocks(self, mock_websearch_adapter, mock_openrouter_adapter):
        """Create pipeline with mocked adapters."""
        pipeline = FactCheckPipeline()
        pipeline.websearch_adapter = mock_websearch_adapter
        pipeline.openrouter_adapter = mock_openrouter_adapter
        return pipeline

    @pytest.mark.asyncio
    async def test_execute_calls_both_steps(self, pipeline_with_mocks):
        """Test that execute calls websearch and evaluation."""
        params = PipelineParams(query="The sky is blue", max_results=5)

        result = await pipeline_with_mocks.execute(params=params)

        # Verify both adapters were called
        pipeline_with_mocks.websearch_adapter.search.assert_called_once_with(
            query="The sky is blue",
            max_results=5,
        )
        pipeline_with_mocks.openrouter_adapter.make_request.assert_called_once()

        # Verify result
        assert isinstance(result, ClaimReview)
        assert result.claimReviewed == "The sky is blue"

    @pytest.mark.asyncio
    async def test_execute_passes_search_results_to_evaluation(
        self, pipeline_with_mocks, mock_websearch_response
    ):
        """Test that search results are passed to evaluation."""
        params = PipelineParams(query="Test claim", max_results=3)

        await pipeline_with_mocks.execute(params=params)

        # Get the call arguments for make_request
        call_args = pipeline_with_mocks.openrouter_adapter.make_request.call_args
        messages = call_args.kwargs["messages"]

        # Verify user message contains search results
        user_message = messages[1]["content"]
        assert "Test claim" in user_message
        assert "NASA confirms sky is blue" in user_message
        assert "https://nasa.gov/sky" in user_message

    @pytest.mark.asyncio
    async def test_execute_uses_correct_model(self, pipeline_with_mocks):
        """Test that correct model is used for evaluation."""
        params = PipelineParams(query="Test", max_results=5)

        await pipeline_with_mocks.execute(params=params)

        call_args = pipeline_with_mocks.openrouter_adapter.make_request.call_args
        assert call_args.kwargs["model"] == "openai/gpt-5.2"
        assert call_args.kwargs["output_type"] == ClaimReview

    @pytest.mark.asyncio
    async def test_execute_includes_system_prompt(self, pipeline_with_mocks):
        """Test that system prompt is included in messages."""
        params = PipelineParams(query="Test", max_results=5)

        await pipeline_with_mocks.execute(params=params)

        call_args = pipeline_with_mocks.openrouter_adapter.make_request.call_args
        messages = call_args.kwargs["messages"]

        assert messages[0]["role"] == "system"
        assert "FactCheckExpert" in messages[0]["content"]
        assert "rating_scale" in messages[0]["content"].lower()


class TestBuildUserPrompt:
    """Tests for _build_user_prompt method."""

    def test_build_user_prompt_includes_claim(self):
        """Test that user prompt includes the claim."""
        pipeline = FactCheckPipeline()
        search_results = [
            WebsearchResponse(
                title="Test",
                url="https://test.com",
                content="Test content",
            )
        ]

        prompt = pipeline._build_user_prompt(
            query="The Earth is round",
            search_results=search_results,
            current_date="2025-01-01",
        )

        assert "The Earth is round" in prompt

    def test_build_user_prompt_includes_search_results(self):
        """Test that user prompt includes search results."""
        pipeline = FactCheckPipeline()
        search_results = [
            WebsearchResponse(
                title="NASA Article",
                url="https://nasa.gov/earth",
                content="The Earth is an oblate spheroid.",
            ),
            WebsearchResponse(
                title="Science Daily",
                url="https://sciencedaily.com/earth",
                content="Scientific evidence confirms Earth's shape.",
            ),
        ]

        prompt = pipeline._build_user_prompt(
            query="Test",
            search_results=search_results,
            current_date="2025-01-01",
        )

        assert "NASA Article" in prompt
        assert "https://nasa.gov/earth" in prompt
        assert "oblate spheroid" in prompt
        assert "Science Daily" in prompt

    def test_build_user_prompt_includes_date(self):
        """Test that user prompt includes current date."""
        pipeline = FactCheckPipeline()

        prompt = pipeline._build_user_prompt(
            query="Test",
            search_results=[],
            current_date="2025-12-25",
        )

        assert "2025-12-25" in prompt

    def test_build_user_prompt_handles_empty_results(self):
        """Test that user prompt handles empty search results."""
        pipeline = FactCheckPipeline()

        prompt = pipeline._build_user_prompt(
            query="Test claim",
            search_results=[],
            current_date="2025-01-01",
        )

        assert "Test claim" in prompt
        assert "Search Results:" in prompt


class TestSearchForEvidence:
    """Tests for _search_for_evidence method."""

    @pytest.mark.asyncio
    async def test_search_for_evidence_calls_adapter(self, mock_websearch_adapter):
        """Test that search calls the websearch adapter."""
        pipeline = FactCheckPipeline()
        pipeline.websearch_adapter = mock_websearch_adapter

        results = await pipeline._search_for_evidence(
            query="Test query",
            max_results=3,
        )

        mock_websearch_adapter.search.assert_called_once_with(
            query="Test query",
            max_results=3,
        )
        assert len(results) == 2  # From mock fixture
