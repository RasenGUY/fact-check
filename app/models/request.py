from pydantic import BaseModel, Field


class FactCheckRequest(BaseModel):
    """Request body for fact-check endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The claim/statement to fact-check",
        examples=["The Great Wall of China is visible from space"],
    )
