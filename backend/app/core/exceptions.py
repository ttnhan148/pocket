"""Custom exception hierarchy for Pocket."""

from __future__ import annotations


class PocketError(Exception):
    """Base exception for all Pocket errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class NotFoundError(PocketError):
    """Entity not found."""

    def __init__(self, entity: str, entity_id: str) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} not found: {entity_id}", "NOT_FOUND")


class ValidationError(PocketError):
    """Business validation failed."""

    def __init__(self, message: str, errors: list[dict[str, str]] | None = None) -> None:
        self.errors = errors or []
        super().__init__(message, "VALIDATION_ERROR")


class ConflictError(PocketError):
    """Duplicate or conflict."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "CONFLICT")


class CircularDependencyError(PocketError):
    """Circular dependency detected in context graph."""

    def __init__(self, path: list[str]) -> None:
        self.path = path
        super().__init__(
            f"Circular dependency detected: {' → '.join(path)}",
            "CIRCULAR_DEPENDENCY",
        )


class PromptValidationError(PocketError):
    """Prompt failed validation checks."""

    def __init__(self, checks: list[dict[str, object]]) -> None:
        self.checks = checks
        super().__init__("Prompt validation failed", "PROMPT_VALIDATION_ERROR")


class AIServiceError(PocketError):
    """Azure OpenAI or AI service error."""

    def __init__(self, message: str, provider: str = "azure_openai") -> None:
        self.provider = provider
        super().__init__(message, "AI_SERVICE_ERROR")


class TokenLimitError(PocketError):
    """Prompt exceeds token limit."""

    def __init__(self, current: int, limit: int) -> None:
        self.current = current
        self.limit = limit
        super().__init__(
            f"Token limit exceeded: {current}/{limit}",
            "TOKEN_LIMIT_EXCEEDED",
        )
