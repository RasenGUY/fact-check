"""Main pipeline orchestrator for fact-checking claims."""

from datetime import datetime

from app.adapters.openrouter_adapter import openrouter_adapter
from app.adapters.openrouter_websearch_adapter import (
    openrouter_websearch_adapter,
    WebsearchResponse,
)
from app.models.response import ClaimReview
from app.models.internal import PipelineParams
from app.config.model_config import ModelSelector, ModelUseCase
from app.pipelines.prompts.evaluation import EVALUATION_PROMPT
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FactCheckPipeline:
    """
    Main pipeline orchestrator for fact-checking claims.

    Pattern: Deterministic 2-step pipeline
    - Step 1: Web search (OpenRouter :online)
    - Step 2: LLM evaluation (structured output)
    """

    def __init__(self):
        self.openrouter_adapter = openrouter_adapter
        self.websearch_adapter = openrouter_websearch_adapter
        self.prompt_mapping = {
            "evaluation": EVALUATION_PROMPT,
        }

    async def execute(self, *, params: PipelineParams) -> ClaimReview:
        """
        Main orchestration method.

        Args:
            params: PipelineParams containing query and max_results

        Returns:
            ClaimReview: Structured fact-check result
        """
        logger.info("Starting fact-check pipeline", query=params.query[:50])

        # Step 1: Web Search (via OpenRouter :online)
        search_results = await self._search_for_evidence(
            query=params.query,
            max_results=params.max_results,
        )

        logger.info("Search complete", num_results=len(search_results))

        # Step 2: LLM Evaluation
        claim_review = await self._evaluate_claim(
            query=params.query,
            search_results=search_results,
        )

        logger.info(
            "Evaluation complete",
            rating=claim_review.reviewRating.ratingValue,
            verdict=claim_review.reviewRating.alternateName,
        )

        return claim_review

    async def _search_for_evidence(
        self,
        *,
        query: str,
        max_results: int = 5,
    ) -> list[WebsearchResponse]:
        """Step 1: Fetch evidence using OpenRouter websearch."""
        return await self.websearch_adapter.search(
            query=query,
            max_results=max_results,
        )

    async def _evaluate_claim(
        self,
        *,
        query: str,
        search_results: list[WebsearchResponse],
    ) -> ClaimReview:
        """Step 2: Evaluate claim using LLM with structured output."""
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Build user message
        user_prompt = self._build_user_prompt(
            query=query,
            search_results=search_results,
            current_date=current_date,
        )

        # Build messages array
        system_prompt = self.prompt_mapping["evaluation"].format(
            current_date=current_date
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Call LLM with structured output
        result = await self.openrouter_adapter.make_request(
            model=ModelSelector.get_model_name(ModelUseCase.FACT_CHECK_EVALUATION),
            messages=messages,
            output_type=ClaimReview,
        )

        return result

    def _build_user_prompt(
        self,
        *,
        query: str,
        search_results: list[WebsearchResponse],
        current_date: str,
    ) -> str:
        """Build the user prompt with claim and evidence."""
        context = "\n\n".join(
            [f"**{r.title}**\nURL: {r.url}\n{r.content}" for r in search_results]
        )

        return f"""
Claim to fact-check:
{query}

Search Results:
{context}

Today's date: {current_date}

Evaluate this claim and return a ClaimReview JSON.
"""


# Singleton instance
fact_check_pipeline = FactCheckPipeline()
