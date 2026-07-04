"""Base classes and types for the AI Prompt Engine Pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class PipelineInput:
    """Input payload for the AI pipeline."""
    user_message: str
    workspace_id: str
    conversation_id: Optional[str] = None
    template_id: Optional[str] = None
    selected_context_ids: Optional[List[str]] = None
    variable_overrides: Optional[Dict[str, str]] = None


@dataclass
class PipelineStepTrace:
    """Trace details for a single executed step."""
    step_name: str
    input_summary: str
    output_summary: str
    duration_ms: int
    status: str  # success | skipped | failed | fallback


@dataclass
class IntentResult:
    """Result of intent detection."""
    intent: str  # question | instruction | creative | analysis | code | conversation
    entities: List[str]
    complexity: str  # simple | moderate | complex
    language: str
    suggested_model: str  # gpt-4.1 | gpt-4.1-mini


@dataclass
class ResolvedVariables:
    """Variables resolved by the pipeline."""
    variables: Dict[str, str]
    unresolved: List[str]
    source_map: Dict[str, str]


@dataclass
class Conflict:
    """Represents a conflict between contexts."""
    context_a_id: str
    context_b_id: str
    conflict_type: str  # duplicate | contradictory | override
    description: str
    resolution: str  # keep_a | keep_b | merge | warn


@dataclass
class ValidationCheck:
    """A single validation rule check result."""
    name: str
    passed: bool
    severity: str  # error | warning | info
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Full validation results."""
    passed: bool
    checks: List[ValidationCheck] = field(default_factory=list)
    errors: List[ValidationCheck] = field(default_factory=list)
    warnings: List[ValidationCheck] = field(default_factory=list)


@dataclass
class PromptScore:
    """Score dimensions evaluated for a prompt."""
    overall: float
    clarity: float
    specificity: float
    completeness: float
    consistency: float
    efficiency: float
    reasoning: str
    suggestions: List[str] = field(default_factory=list)


@dataclass
class CritiqueResult:
    """AI Critique result."""
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    overall_assessment: str = ""


@dataclass
class TokenUsage:
    """Token counting metrics."""
    prompt: int
    completion: int
    total: int


@dataclass
class ContextUsed:
    """Information about context blocks that were compile-inserted."""
    id: str
    title: str
    score: float


@dataclass
class PipelineOutput:
    """Final output of the completed pipeline execution."""
    final_prompt: str
    system_prompt: str
    ai_response: str
    contexts_used: List[ContextUsed] = field(default_factory=list)
    variables_resolved: Dict[str, str] = field(default_factory=dict)
    validation_result: Optional[ValidationResult] = None
    prompt_score: Optional[PromptScore] = None
    token_usage: Optional[TokenUsage] = None
    cost: float = 0.0
    latency_ms: int = 0
    pipeline_trace: List[PipelineStepTrace] = field(default_factory=list)


@dataclass
class PipelineContext:
    """Internal state carried through the pipeline."""
    input: PipelineInput
    intent: Optional[IntentResult] = None
    selected_model: Optional[str] = None
    workspace: Optional[Any] = None
    resolved_variables: Optional[ResolvedVariables] = None
    retrieved_contexts: List[Any] = field(default_factory=list)
    ordered_contexts: List[Any] = field(default_factory=list)
    ranked_contexts: List[Any] = field(default_factory=list)
    system_prompt: str = ""
    compiled_messages: List[Dict[str, str]] = field(default_factory=list)
    final_prompt: str = ""
    validation_result: Optional[ValidationResult] = None
    prompt_score: Optional[PromptScore] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)
    optimization_applied: bool = False
    enhancement_notes: List[str] = field(default_factory=list)
    critique: Optional[CritiqueResult] = None


class PipelineStep:
    """Base class for any step executing within the AI pipeline."""
    name: str = "pipeline_step"

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """Executes the pipeline step. Override in subclasses."""
        raise NotImplementedError

    def fallback(self, ctx: PipelineContext) -> PipelineContext:
        """Provides graceful degradation fallback logic. Override if needed."""
        return ctx

    def summarize_input(self, ctx: PipelineContext) -> str:
        """Summarizes step input state for logging/tracing."""
        return ""

    def summarize_output(self, ctx: PipelineContext) -> str:
        """Summarizes step output state for logging/tracing."""
        return ""


class PipelineStepError(Exception):
    """Base exception for errors inside pipeline steps."""
    pass


class ValidationFailedError(PipelineStepError):
    """Raised when validation fails and blocks pipeline execution."""
    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        super().__init__(f"Prompt validation failed with {len(result.errors)} errors.")
