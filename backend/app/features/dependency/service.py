"""Business logic service for Context Dependencies (DAG management with cycle detection)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.service import BaseService
from app.features.context.repository import ContextRepository
from app.features.dependency.schemas import (
    ContextDependencyNode,
    DependencyCreate,
    DependencyEdgeResponse,
    DependencyGraphResponse,
)
from app.models import ContextDependency


class DependencyService(BaseService):
    """Manages context dependencies, detects circular references, and performs topological sorting."""

    def __init__(self, db: Any) -> None:
        super().__init__(db)
        self.context_repo = ContextRepository(db)

    async def add_dependency(
        self, workspace_id: str, source_id: str, data: DependencyCreate
    ) -> ContextDependency:
        """Create a directed dependency edge. Validates self-reference and cycle avoidance."""
        if source_id == data.target_id:
            raise ValidationError("A context cannot depend on itself.")

        # Ensure both contexts exist in the workspace
        source = await self.context_repo.get_or_raise(source_id)
        if source.workspace_id != workspace_id:
            raise NotFoundError("Context", source_id)

        target = await self.context_repo.get_or_raise(data.target_id)
        if target.workspace_id != workspace_id:
            raise NotFoundError("Context", data.target_id)

        # Check if relationship already exists
        exist_stmt = select(ContextDependency).where(
            ContextDependency.source_id == source_id,
            ContextDependency.target_id == data.target_id,
            ContextDependency.deleted_at.is_(None),
        )
        res = await self.db.execute(exist_stmt)
        if res.scalar_one_or_none():
            raise ConflictError("Dependency relationship already exists.")

        # Temporarily check if introducing this edge creates a cycle
        # We can run a DFS starting from target_id to see if source_id is reachable.
        # If reachable, adding source_id -> target_id would form a cycle.
        if await self._path_exists(start_id=data.target_id, end_id=source_id):
            raise ValidationError("Circular dependency detected. Action rejected.")

        dep = ContextDependency(
            source_id=source_id,
            target_id=data.target_id,
            dependency_type=data.dependency_type,
            weight=data.weight,
            description=data.description,
        )
        self.db.add(dep)
        await self.db.flush()
        return dep

    async def remove_dependency(self, workspace_id: str, source_id: str, target_id: str) -> None:
        """Delete dependency edge between source and target contexts."""
        stmt = select(ContextDependency).where(
            ContextDependency.source_id == source_id,
            ContextDependency.target_id == target_id,
            ContextDependency.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        dep = res.scalar_one_or_none()
        if not dep:
            raise NotFoundError("ContextDependency", f"{source_id}->{target_id}")

        # Eagerly soft delete or hard delete the edge
        await self.db.delete(dep)
        await self.db.flush()

    async def get_dependencies(self, workspace_id: str, context_id: str) -> list[ContextDependency]:
        """Get list of immediate dependencies target contexts for a given context."""
        stmt = select(ContextDependency).where(
            ContextDependency.source_id == context_id,
            ContextDependency.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_graph(self, workspace_id: str) -> DependencyGraphResponse:
        """Construct the entire dependency graph (DAG) for the workspace and retrieve topological order."""
        # 1. Load all active contexts in workspace
        contexts = await self.context_repo.list_by_workspace(workspace_id=workspace_id, limit=1000)
        context_map = {c.id: c for c in contexts}

        # 2. Load all active dependency edges in this workspace
        context_ids = list(context_map.keys())
        edges: list[ContextDependency] = []
        if context_ids:
            edge_stmt = select(ContextDependency).where(
                ContextDependency.source_id.in_(context_ids),
                ContextDependency.deleted_at.is_(None),
            )
            edge_res = await self.db.execute(edge_stmt)
            edges = list(edge_res.scalars().all())

        # Filter edges where target is also in active contexts
        valid_edges = [e for e in edges if e.target_id in context_map]

        # 3. Build Adjacency List & Indegree calculations
        # If A is a dependency of B (B -> A), then B depends on A.
        # This means A must be resolved before B.
        # The dependency graph direction is A -> B.
        adj = defaultdict(list)
        indegree = dict.fromkeys(context_ids, 0)
        for e in valid_edges:
            # target_id (the dependency) -> source_id (the dependent context)
            adj[e.target_id].append(e.source_id)
            indegree[e.source_id] += 1

        # 4. Kahn's algorithm for topological sorting
        # Contexts with 0 indegree can be resolved first (leaves/independent)
        queue = [cid for cid in context_ids if indegree[cid] == 0]
        topo_order: list[str] = []

        while queue:
            curr = queue.pop(0)
            topo_order.append(curr)
            for neighbor in adj[curr]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        # Handle cycles gracefully (should not happen due to insert validation, but safety check)
        if len(topo_order) < len(context_ids):
            # Append remaining items that are part of cycle or unreachable
            remaining = [cid for cid in context_ids if cid not in topo_order]
            topo_order.extend(remaining)

        # 5. Populate response schemas
        nodes_resp = [
            ContextDependencyNode(
                id=c.id,
                title=c.title,
                slug=c.slug,
                context_type=c.context_type,
            )
            for c in contexts
        ]
        edges_resp = [
            DependencyEdgeResponse(
                source_id=e.source_id,
                target_id=e.target_id,
                dependency_type=e.dependency_type,
                weight=e.weight,
            )
            for e in valid_edges
        ]

        return DependencyGraphResponse(
            nodes=nodes_resp,
            edges=edges_resp,
            topological_order=topo_order,
        )

    async def _path_exists(self, start_id: str, end_id: str, visited: set[str] | None = None) -> bool:
        """DFS utility to check if there is a path from start_id to end_id."""
        if start_id == end_id:
            return True
        if visited is None:
            visited = set()
        visited.add(start_id)

        # Find immediate dependency targets
        stmt = select(ContextDependency).where(
            ContextDependency.source_id == start_id,
            ContextDependency.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        neighbors = [dep.target_id for dep in res.scalars().all()]

        for neighbor in neighbors:
            if neighbor not in visited and await self._path_exists(neighbor, end_id, visited):
                return True
        return False
