from pydantic import BaseModel, Field
from typing import List


class Organization(BaseModel):
    """Schema.org Organization."""
    name: str = Field(default="WordLift")


class Rating(BaseModel):
    """Schema.org Rating."""
    ratingValue: str = Field(..., description="0-5 rating")
    alternateName: str = Field(..., description="Human-readable verdict")
    bestRating: str = Field(default="5")
    worstRating: str = Field(default="1")


class ItemReviewed(BaseModel):
    """Schema.org CreativeWork for sources."""
    url: List[str] = Field(..., description="Source URLs used")


class ClaimReview(BaseModel):
    """Schema.org ClaimReview - the main output."""
    claimReviewed: str = Field(..., description="The exact claim checked")
    author: Organization = Field(default_factory=Organization)
    datePublished: str = Field(..., description="YYYY-MM-DD format")
    reviewRating: Rating
    url: str = Field(..., description="URL to the fact-check page")
    reviewBody: str = Field(..., description="Explanation of verdict")
    itemReviewed: ItemReviewed

    class Config:
        populate_by_name = True
