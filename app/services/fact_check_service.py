from app.models.request import FactCheckRequest
from app.models.response import ClaimReview
from app.models.internal import PipelineParams
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FactCheckService:
    """
    Service layer between API and Pipeline.

    Responsibilities:
    - Convert API request to pipeline params
    - Handle any pre/post processing
    - Dependency injection point
    """

    def __init__(self, pipeline=None):
        # Pipeline will be injected in Phase 6
        self.pipeline = pipeline

    async def fact_check(self, *, request: FactCheckRequest) -> ClaimReview:
        """
        Execute fact-check for a given request.

        Args:
            request: FactCheckRequest from API

        Returns:
            ClaimReview: Structured fact-check result
        """
        logger.info("Processing fact-check request", query=request.query[:50])

        params = PipelineParams(
            query=request.query,
            max_results=5,
        )

        # TODO: Replace with actual pipeline call in Phase 6
        # return await self.pipeline.execute(params=params)

        # For now, return a stub response
        from datetime import datetime
        from app.models.response import Rating, ItemReviewed

        return ClaimReview(
            claimReviewed=request.query,
            datePublished=datetime.now().strftime("%Y-%m-%d"),
            reviewRating=Rating(
                ratingValue="3",
                alternateName="Half True",
            ),
            url=f"https://fact-check.wordlift.io/review/{request.query[:30].lower().replace(' ', '-')}",
            reviewBody="This is a stub response from FactCheckService. The actual pipeline will be integrated in Phase 6.",
            itemReviewed=ItemReviewed(
                url=["https://example.com/source1", "https://example.com/source2"]
            ),
        )


# Default service instance
fact_check_service = FactCheckService()
