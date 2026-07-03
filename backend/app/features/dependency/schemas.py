"""Context Dependency Pydantic validation schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DependencyCreate(BaseModel):
    """Request schema for creating a directed dependency between contexts."""

    target_id: str = Field(..., description="The ID of the target context we depend on")
    dependency_type: str = Field("requires", description="'requires', 'extends', 'overrides', or 'complements'")
    weight: float = Field(1.0, ge=0.0, description="Relative weight of dependency relevance")
    description: str | None = Field(None, max_length=500, description="Optional description of connection reason")


class DependencyResponse(BaseModel):
    """Response schema for ContextDependency queries."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    target_id: str
    dependency_type: str
    weight: float
    description: str | None
    created_at: datetime


class ContextDependencyNode(BaseModel):
    """Simplified node metadata for dependency graph visualization."""

    id: str
    title: str
    slug: str
    context_type: str


class DependencyEdgeResponse(BaseModel):
    """Directed edge description for dependency graph visualization."""

    source_id: str
    target_id: str
    dependency_type: str
    weight: float


class DependencyGraphResponse(BaseModel):
    """ Adjacency representation of the directed acyclic context graph (DAG)."""

    nodes: list[ContextDependencyNode]
    edges: list[DependencyEdgeResponse]
    topological_order: list[str] = Field(..., description="Workspace context IDs sorted in topological validation order")
