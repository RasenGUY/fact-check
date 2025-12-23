from app.models.request import FactCheckRequest
from app.models.response import ClaimReview
from app.models.internal import PipelineParams
from app.pipelines.fact_check_pipeline import fact_check_pipeline
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
        self.pipeline = pipeline or fact_check_pipeline

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

        return await self.pipeline.execute(params=params)


# Default service instance
fact_check_service = FactCheckService()
