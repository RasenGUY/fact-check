from pydantic import BaseModel, Field


class PipelineParams(BaseModel):
    """Parameters for pipeline execution."""

    query: str = Field(..., description="Claim to fact-check")
    max_results: int = Field(default=5, ge=1, le=10)
