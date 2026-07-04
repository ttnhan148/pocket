"""Pydantic schemas for Search feature API."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """A single matched search result entity."""
    id: str = Field(..., description="UUID of the matched entity")
    title: str = Field(..., description="Title or name of the entity")
    type: str = Field(..., description="Entity type: context | template | conversation")
    score: float = Field(..., description="Search score (0.0 to 1.0, higher is more relevant)")
    subtitle: Optional[str] = Field(None, description="Short context/category/model description")
    description: Optional[str] = Field(None, description="Short snippet or content description")


class SearchResponse(BaseModel):
    """Consolidated list of search results."""
    results: list[SearchResultItem] = Field(..., description="List of search results sorted by relevance score")
