"""Unit tests for FactCheckService."""

import pytest
from unittest.mock import AsyncMock

from app.services.fact_check_service import FactCheckService
from app.models.request import FactCheckRequest
from app.models.response import ClaimReview
from app.models.internal import PipelineParams


class TestFactCheckService:
    """Tests for FactCheckService."""

    @pytest.mark.asyncio
    async def test_fact_check_calls_pipeline(self, mock_pipeline, mock_claim_review):
        """Test that fact_check calls the pipeline."""
        service = FactCheckService(pipeline=mock_pipeline)
        request = FactCheckRequest(query="The sky is blue")

        result = await service.fact_check(request=request)

        mock_pipeline.execute.assert_called_once()
        assert isinstance(result, ClaimReview)

    @pytest.mark.asyncio
    async def test_fact_check_passes_correct_params(self, mock_pipeline):
        """Test that correct params are passed to pipeline."""
        service = FactCheckService(pipeline=mock_pipeline)
        request = FactCheckRequest(query="Test claim for verification")

        await service.fact_check(request=request)

        call_args = mock_pipeline.execute.call_args
        params = call_args.kwargs["params"]

        assert isinstance(params, PipelineParams)
        assert params.query == "Test claim for verification"
        assert params.max_results == 5

    @pytest.mark.asyncio
    async def test_fact_check_returns_pipeline_result(self, mock_pipeline, mock_claim_review):
        """Test that service returns pipeline result."""
        service = FactCheckService(pipeline=mock_pipeline)
        request = FactCheckRequest(query="Test")

        result = await service.fact_check(request=request)

        assert result == mock_claim_review
        assert result.claimReviewed == "The sky is blue"
        assert result.reviewRating.ratingValue == "5"

    @pytest.mark.asyncio
    async def test_service_uses_default_pipeline_when_none_provided(self):
        """Test that service uses default pipeline when none provided."""
        service = FactCheckService()

        # Should not raise - uses default pipeline
        assert service.pipeline is not None

    @pytest.mark.asyncio
    async def test_service_accepts_custom_pipeline(self, mock_pipeline):
        """Test that service accepts custom pipeline via dependency injection."""
        service = FactCheckService(pipeline=mock_pipeline)

        assert service.pipeline is mock_pipeline
