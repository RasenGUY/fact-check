from pydantic import BaseModel, Field
from typing import List


class Organization(BaseModel):
    """Schema.org Organization."""

    type: str = Field(default="Organization", alias="@type")
    name: str = Field(default="WordLift")


class Rating(BaseModel):
    """Schema.org Rating."""

    type: str = Field(default="Rating", alias="@type")
    ratingValue: str = Field(..., description="0-5 rating")
    alternateName: str = Field(..., description="Human-readable verdict")
    bestRating: str = Field(default="5")
    worstRating: str = Field(default="1")


class ItemReviewed(BaseModel):
    """Schema.org CreativeWork for sources."""

    type: str = Field(default="CreativeWork", alias="@type")
    url: List[str] = Field(..., description="Source URLs used")


class ClaimReview(BaseModel):
    """Schema.org ClaimReview - the main output."""

    context: str = Field(default="http://schema.org", alias="@context")
    type: str = Field(default="ClaimReview", alias="@type")
    claimReviewed: str = Field(..., description="The exact claim checked")
    author: Organization = Field(default_factory=Organization)
    datePublished: str = Field(..., description="YYYY-MM-DD format")
    reviewRating: Rating
    url: str = Field(..., description="URL to the fact-check page")
    reviewBody: str = Field(..., description="Explanation of verdict")
    itemReviewed: ItemReviewed

    class Config:
        populate_by_name = True
