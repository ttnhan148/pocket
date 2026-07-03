"""Tags and Categories Service layer."""

from __future__ import annotations

from typing import Any

from slugify import slugify

from app.core.exceptions import ConflictError, ValidationError
from app.core.service import BaseService
from app.features.tags_categories.repository import CategoryRepository, TagRepository
from app.features.tags_categories.schemas import (
    CategoryCreate,
    CategoryTreeResponse,
    CategoryUpdate,
    TagCreate,
    TagUpdate,
)
from app.models import Category, Tag


class TagService(BaseService):
    """Business logic for Tags."""

    def __init__(self, db: Any) -> None:
        super().__init__(db)
        self.repo = TagRepository(db)

    async def create_tag(self, data: TagCreate) -> Tag:
        """Create a new tag. Returns existing tag if matching slug is found."""
        slug = slugify(data.name)
        existing = await self.repo.get_by_slug(slug)
        if existing:
            return existing

        tag = Tag(name=data.name, slug=slug, color=data.color, usage_count=0)
        return await self.repo.create(tag)

    async def get_tag(self, tag_id: str) -> Tag:
        """Fetch tag by ID or raise NotFoundError."""
        return await self.repo.get_or_raise(tag_id)

    async def list_tags(self, skip: int = 0, limit: int = 100) -> list[Tag]:
        """List active tags."""
        return await self.repo.list(skip, limit)

    async def update_tag(self, tag_id: str, data: TagUpdate) -> Tag:
        """Update fields of a tag."""
        tag = await self.get_tag(tag_id)
        update_dict: dict[str, Any] = {}

        if data.name is not None and data.name != tag.name:
            slug = slugify(data.name)
            existing = await self.repo.get_by_slug(slug)
            if existing and existing.id != tag_id:
                raise ConflictError(f"Tag with slug '{slug}' already exists")
            update_dict["name"] = data.name
            update_dict["slug"] = slug

        if data.color is not None:
            update_dict["color"] = data.color

        return await self.repo.update(tag_id, update_dict)

    async def delete_tag(self, tag_id: str) -> bool:
        """Soft delete a tag."""
        return await self.repo.delete(tag_id, soft=True)


class CategoryService(BaseService):
    """Business logic for Categories tree folder navigation."""

    def __init__(self, db: Any) -> None:
        super().__init__(db)
        self.repo = CategoryRepository(db)

    async def create_category(self, data: CategoryCreate) -> Category:
        """Create a Category folder, checking parent and slug validity."""
        if data.parent_id:
            await self.repo.get_or_raise(data.parent_id)

        slug = slugify(data.name)
        existing = await self.repo.get_by_slug(slug)
        if existing:
            original_slug = slug
            counter = 2
            while existing:
                slug = f"{original_slug}-{counter}"
                existing = await self.repo.get_by_slug(slug)
                counter += 1

        category = Category(
            name=data.name,
            slug=slug,
            description=data.description,
            icon=data.icon,
            color=data.color,
            sort_order=data.sort_order,
            parent_id=data.parent_id,
        )
        return await self.repo.create(category)

    async def get_category(self, category_id: str) -> Category:
        """Retrieve category by ID or raise NotFoundError."""
        return await self.repo.get_or_raise(category_id)

    async def update_category(self, category_id: str, data: CategoryUpdate) -> Category:
        """Update category, preventing self-referential or descendant hierarchical cycles."""
        category = await self.get_category(category_id)
        update_dict: dict[str, Any] = {}

        if data.name is not None and data.name != category.name:
            slug = slugify(data.name)
            existing = await self.repo.get_by_slug(slug)
            if existing and existing.id != category_id:
                raise ConflictError(f"Category with slug '{slug}' already exists")
            update_dict["name"] = data.name
            update_dict["slug"] = slug

        if data.parent_id is not None:
            if data.parent_id == category_id:
                raise ValidationError("A category cannot be its own parent")
            if data.parent_id:
                # Check for cycle (if target parent is a descendant of this category)
                if await self._is_descendant(child_id=data.parent_id, parent_id=category_id):
                    raise ValidationError("Hierarchy cycle detected: target parent is a descendant")
                await self.repo.get_or_raise(data.parent_id)
            update_dict["parent_id"] = data.parent_id or None

        if data.description is not None:
            update_dict["description"] = data.description
        if data.icon is not None:
            update_dict["icon"] = data.icon
        if data.color is not None:
            update_dict["color"] = data.color
        if data.sort_order is not None:
            update_dict["sort_order"] = data.sort_order

        return await self.repo.update(category_id, update_dict)

    async def delete_category(self, category_id: str) -> bool:
        """Soft delete a category folder."""
        # Unlink children by setting parent_id to Null, or delete recursively.
        # We unlink children to keep their subtrees alive at root level (soft cascade safety)
        children = await self.repo.list_children(category_id)
        for child in children:
            child.parent_id = None
        await self.db.flush()

        return await self.repo.delete(category_id, soft=True)

    async def _is_descendant(self, child_id: str, parent_id: str) -> bool:
        """Recursively checks if child_id is a descendant of parent_id."""
        child = await self.repo.get(child_id)
        if not child or not child.parent_id:
            return False
        if child.parent_id == parent_id:
            return True
        return await self._is_descendant(child.parent_id, parent_id)

    async def get_category_tree(self) -> list[CategoryTreeResponse]:
        """Fetch full workspace category tree hierarchy."""
        roots = await self.repo.list_roots()
        tree: list[CategoryTreeResponse] = []
        for root in roots:
            node = await self._build_tree_node(root)
            tree.append(node)
        return tree

    async def _build_tree_node(self, category: Category) -> CategoryTreeResponse:
        """Recursively construct a tree node with child categories."""
        children_records = await self.repo.list_children(category.id)
        children: list[CategoryTreeResponse] = []
        for child in children_records:
            node = await self._build_tree_node(child)
            children.append(node)

        return CategoryTreeResponse(
            id=category.id,
            slug=category.slug,
            name=category.name,
            description=category.description,
            icon=category.icon,
            color=category.color,
            sort_order=category.sort_order,
            parent_id=category.parent_id,
            created_at=category.created_at,
            updated_at=category.updated_at,
            children=children,
        )
