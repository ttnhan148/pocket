"""Models package exports all database models for SQLAlchemy metadata imports."""

from __future__ import annotations

from app.models.analytics import AnalyticsEvent, AuditLog
from app.models.base import Base, BaseModel
from app.models.context import (
    Category,
    Context,
    ContextDependency,
    ContextEmbedding,
    ContextHealthScore,
    ContextUsage,
    ContextVersion,
    Tag,
    context_tags,
)
from app.models.conversation import Conversation, Message
from app.models.journal import Journal
from app.models.learning import ContextCandidate, LearningRecord
from app.models.prompt import PromptContext, PromptRun, PromptScore, PromptVersion
from app.models.provider import Provider
from app.models.settings import Favorite, Setting
from app.models.template import Template, TemplateVariable, TemplateVersion
from app.models.variable import Variable, WorkspaceVariable
from app.models.workspace import Workspace, WorkspaceSettings
from app.models.ai_job import AIJob, AIJobResult

__all__ = [
    "AIJob",
    "AIJobResult",
    "AnalyticsEvent",
    "AuditLog",
    "Base",
    "BaseModel",
    "Category",
    "Context",
    "ContextCandidate",
    "ContextDependency",
    "ContextEmbedding",
    "ContextHealthScore",
    "ContextUsage",
    "ContextVersion",
    "Conversation",
    "Favorite",
    "Journal",
    "LearningRecord",
    "Message",
    "PromptContext",
    "PromptRun",
    "PromptScore",
    "PromptVersion",
    "Provider",
    "Setting",
    "Tag",
    "Template",
    "TemplateVariable",
    "TemplateVersion",
    "Variable",
    "Workspace",
    "WorkspaceSettings",
    "WorkspaceVariable",
    "context_tags",
]
