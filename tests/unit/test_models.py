"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from app.models.request import FactCheckRequest
from app.models.response import ClaimReview, Rating, ItemReviewed, Organization
from app.models.internal import PipelineParams


class TestFactCheckRequest:
    """Tests for FactCheckRequest model."""

    def test_valid_request(self):
        """Test creating a valid request."""
        req = FactCheckRequest(query="The sky is blue")
        assert req.query == "The sky is blue"

    def test_empty_query_rejected(self):
        """Test that empty query is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FactCheckRequest(query="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_query_max_length(self):
        """Test that query exceeding max length is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FactCheckRequest(query="x" * 1001)
        assert "String should have at most 1000 characters" in str(exc_info.value)

    def test_query_at_max_length(self):
        """Test query at exactly max length is accepted."""
        req = FactCheckRequest(query="x" * 1000)
        assert len(req.query) == 1000


class TestRating:
    """Tests for Rating model."""

    def test_valid_rating(self):
        """Test creating a valid rating."""
        rating = Rating(ratingValue="5", alternateName="True")
        assert rating.ratingValue == "5"
        assert rating.alternateName == "True"
        assert rating.bestRating == "5"
        assert rating.worstRating == "1"

    def test_rating_default_values(self):
        """Test rating default values."""
        rating = Rating(ratingValue="3", alternateName="Half True")
        assert rating.bestRating == "5"
        assert rating.worstRating == "1"


class TestItemReviewed:
    """Tests for ItemReviewed model."""

    def test_valid_item_reviewed(self):
        """Test creating a valid item reviewed."""
        item = ItemReviewed(url=["https://example.com", "https://test.com"])
        assert len(item.url) == 2

    def test_item_reviewed_urls(self):
        """Test item reviewed contains provided URLs."""
        item = ItemReviewed(url=["https://example.com"])
        assert "https://example.com" in item.url


class TestOrganization:
    """Tests for Organization model."""

    def test_default_organization(self):
        """Test default organization values."""
        org = Organization()
        assert org.name == "WordLift"

    def test_custom_organization_name(self):
        """Test organization with custom name."""
        org = Organization(name="CustomOrg")
        assert org.name == "CustomOrg"


class TestClaimReview:
    """Tests for ClaimReview model."""

    def test_valid_claim_review(self):
        """Test creating a valid claim review."""
        review = ClaimReview(
            claimReviewed="Test claim",
            datePublished="2025-01-01",
            reviewRating=Rating(ratingValue="5", alternateName="True"),
            url="https://fact-check.wordlift.io/review/test",
            reviewBody="This claim is verified as true.",
            itemReviewed=ItemReviewed(url=["https://source.com"]),
        )
        assert review.claimReviewed == "Test claim"
        assert review.reviewRating.ratingValue == "5"

    def test_claim_review_default_author(self):
        """Test claim review default author value."""
        review = ClaimReview(
            claimReviewed="Test",
            datePublished="2025-01-01",
            reviewRating=Rating(ratingValue="3", alternateName="Half True"),
            url="https://example.com/review",
            reviewBody="Test body",
            itemReviewed=ItemReviewed(url=["https://source.com"]),
        )
        assert review.author.name == "WordLift"

    def test_claim_review_with_custom_author(self):
        """Test claim review with custom author."""
        review = ClaimReview(
            claimReviewed="Test",
            datePublished="2025-01-01",
            reviewRating=Rating(ratingValue="5", alternateName="True"),
            url="https://example.com",
            reviewBody="Body",
            itemReviewed=ItemReviewed(url=["https://source.com"]),
            author=Organization(name="CustomOrg"),
        )
        assert review.author.name == "CustomOrg"


class TestPipelineParams:
    """Tests for PipelineParams model."""

    def test_valid_params(self):
        """Test creating valid pipeline params."""
        params = PipelineParams(query="Test query", max_results=5)
        assert params.query == "Test query"
        assert params.max_results == 5

    def test_default_max_results(self):
        """Test default max_results value."""
        params = PipelineParams(query="Test")
        assert params.max_results == 5

    def test_max_results_bounds(self):
        """Test max_results validation bounds."""
        with pytest.raises(ValidationError):
            PipelineParams(query="Test", max_results=0)

        with pytest.raises(ValidationError):
            PipelineParams(query="Test", max_results=11)

    def test_max_results_at_bounds(self):
        """Test max_results at valid bounds."""
        params_min = PipelineParams(query="Test", max_results=1)
        assert params_min.max_results == 1

        params_max = PipelineParams(query="Test", max_results=10)
        assert params_max.max_results == 10
