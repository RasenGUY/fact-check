from fastapi import APIRouter

from app.models.request import FactCheckRequest
from app.models.response import ClaimReview
from app.services.fact_check_service import fact_check_service

router = APIRouter()


@router.post("/fact-check", response_model=ClaimReview)
async def fact_check(request: FactCheckRequest) -> ClaimReview:
    """
    Fact-check a claim and return structured verdict.
    """
    return await fact_check_service.fact_check(request=request)
