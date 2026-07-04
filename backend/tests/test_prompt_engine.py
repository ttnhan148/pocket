"""Unit and integration tests for Prompt Engine pipeline steps (M25-M32)."""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.ai.client import AzureAIClient, ChatResult
from app.ai.pipeline import (
    Conflict,
    ContextUsed,
    IntentResult,
    PipelineContext,
    PipelineInput,
    PipelineOrchestrator,
    PipelineStepError,
    PromptCompiler,
    PromptCritic,
    PromptEnhancer,
    PromptOptimizer,
    PromptScorer,
    TokenCounter,
    ValidationCheck,
    ValidationEngine,
    ValidationFailedError,
    ValidationResult,
)
from app.models import Context, ContextDependency, Workspace


def test_token_counter() -> None:
    """Verify tiktoken token counting behaves as expected."""
    settings = Settings(azure_openai_api_key="mock", azure_openai_endpoint="http://mock")
    counter = TokenCounter(settings)

    # Basic string counting
    assert counter.count("") == 0
    assert counter.count("hello") > 0

    # Truncate check
    long_text = "hello world how are you today"
    truncated = counter.truncate_text(long_text, max_tokens=3)
    assert counter.count(truncated) <= 3


@pytest.mark.asyncio
async def test_intent_detector() -> None:
    """Verify IntentDetector classifies intent and handles fallbacks."""
    ai_client = MagicMock(spec=AzureAIClient)
    ai_client.chat_json = AsyncMock(return_value={
        "intent": "code",
        "entities": ["python", "pytest"],
        "complexity": "complex",
        "language": "en",
        "suggested_model": "gpt-4.1",
    })
    settings = Settings(azure_openai_endpoint="http://mock", azure_openai_deployment_chat="gpt-4.1", azure_openai_deployment_chat_mini="gpt-4.1-mini")
    
    from app.ai.pipeline.intent import IntentDetector
    detector = IntentDetector(ai_client, settings)

    ctx = PipelineContext(input=PipelineInput(user_message="write test code", workspace_id="ws-1"))
    ctx = await detector.execute(ctx)

    assert ctx.intent is not None
    assert ctx.intent.intent == "code"
    assert ctx.intent.complexity == "complex"
    assert ctx.selected_model == "gpt-4.1"


@pytest.mark.asyncio
async def test_intent_detector_fallback() -> None:
    """Verify IntentDetector falls back gracefully when AI connection fails."""
    ai_client = MagicMock(spec=AzureAIClient)
    ai_client.chat_json = AsyncMock(side_effect=Exception("Azure OpenAI offline"))
    settings = Settings(azure_openai_endpoint="http://mock", azure_openai_deployment_chat="gpt-4.1")

    from app.ai.pipeline.intent import IntentDetector
    detector = IntentDetector(ai_client, settings)

    ctx = PipelineContext(input=PipelineInput(user_message="hello", workspace_id="ws-1"))
    ctx = await detector.execute(ctx)

    assert ctx.intent is not None
    assert ctx.intent.intent == "instruction"
    assert ctx.selected_model == "gpt-4.1"


@pytest.mark.asyncio
async def test_prompt_compiler() -> None:
    """Verify PromptCompiler sorts, renders variables, and merges history."""
    compiler = PromptCompiler()

    # Create mock contexts of different types
    c1 = MagicMock(spec=Context)
    c1.context_type = "persona"
    c1.content = "You are a math tutor."
    c1.title = "Math Tutor"

    c2 = MagicMock(spec=Context)
    c2.context_type = "instruction"
    c2.content = "Explain {{ topic }} clearly."
    c2.title = "Explain Topic"

    ctx = PipelineContext(input=PipelineInput(user_message="solve 2+2", workspace_id="ws-1"))
    
    # We populate retrieved_contexts directly
    ctx.retrieved_contexts = [c2, c1]  # out of order
    
    # Mock resolved variables
    from app.ai.pipeline.base import ResolvedVariables
    ctx.resolved_variables = ResolvedVariables(
        variables={"topic": "algebra"},
        unresolved=[],
        source_map={}
    )

    ctx = await compiler.execute(ctx)

    # Check compile order: persona should be before instruction
    assert "## PERSONA\n\nYou are a math tutor." in ctx.system_prompt
    assert "## INSTRUCTION\n\nExplain algebra clearly." in ctx.system_prompt
    assert ctx.compiled_messages[0]["role"] == "system"
    assert ctx.compiled_messages[1]["role"] == "user"


@pytest.mark.asyncio
async def test_prompt_optimizer() -> None:
    """Verify PromptOptimizer cleans whitespace, deduplicates, and priorities constraints."""
    ai_client = MagicMock(spec=AzureAIClient)
    settings = Settings(azure_openai_endpoint="http://mock", ai_optimization_enabled=False)
    optimizer = PromptOptimizer(ai_client, settings)

    ctx = PipelineContext(input=PipelineInput(user_message="test", workspace_id="ws-1"))
    # Duplicate sections, extra blanks, incorrect priorities
    ctx.final_prompt = (
        "## CONSTRAINT\n"
        "You should speak quietly.\n"
        "You must speak clearly.\n"
        "\n\n"
        "You must speak clearly.\n"
    )
    ctx.compiled_messages = [{"role": "system", "content": ctx.final_prompt}]

    ctx = await optimizer.execute(ctx)

    # Check normalization: duplicate paragraphs removed, must comes before should
    assert ctx.final_prompt.count("You must speak clearly.") == 1
    assert "You must speak clearly.\nYou should speak quietly." in ctx.final_prompt


@pytest.mark.asyncio
async def test_validation_engine() -> None:
    """Verify ValidationEngine flags error when unresolved variables remain."""
    ai_client = MagicMock(spec=AzureAIClient)
    settings = Settings(azure_openai_endpoint="http://mock", token_limit=100)
    counter = TokenCounter(settings)
    
    validator = ValidationEngine(ai_client, counter, settings)

    ctx = PipelineContext(input=PipelineInput(user_message="hello", workspace_id="ws-1"))
    ctx.final_prompt = "Hello {{ missing_var }}!"
    ctx.compiled_messages = [{"role": "system", "content": ctx.final_prompt}]
    
    # Run and verify it raises ValidationFailedError due to unresolved variable
    with pytest.raises(ValidationFailedError) as exc_info:
        await validator.execute(ctx)
        
    assert "missing_variables" in [err.name for err in exc_info.value.result.errors]


@pytest.mark.asyncio
async def test_dependency_resolver_topological_sort() -> None:
    """Verify Kahn's topological sort arranges contexts correctly and catches circular dependencies."""
    db = MagicMock(spec=AsyncSession)

    c1 = MagicMock(spec=Context)
    c1.id = "ctx-1"
    c1.context_type = "persona"
    c1.title = "Persona"

    c2 = MagicMock(spec=Context)
    c2.id = "ctx-2"
    c2.context_type = "instruction"
    c2.title = "Instruction"

    # Edge: c2 depends on c1 (c1 must come first)
    edge = MagicMock(spec=ContextDependency)
    edge.source_id = "ctx-2"
    edge.target_id = "ctx-1"
    edge.deleted_at = None

    # Mock database session execution
    db.execute = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[edge])))
    db.execute.return_value = mock_result

    from app.ai.pipeline.orchestrator import DependencyResolver
    resolver = DependencyResolver(db)

    ctx = PipelineContext(input=PipelineInput(user_message="test", workspace_id="ws-1"))
    ctx.retrieved_contexts = [c2, c1]

    ctx = await resolver.execute(ctx)

    # c1 (target) must come before c2 (source)
    assert ctx.ordered_contexts[0].id == "ctx-1"
    assert ctx.ordered_contexts[1].id == "ctx-2"


@pytest.mark.asyncio
async def test_pipeline_orchestrator_lifecycle() -> None:
    """Verify that the full orchestrator completes end-to-end runs successfully."""
    db = MagicMock(spec=AsyncSession)
    settings = Settings(
        azure_openai_endpoint="http://mock",
        azure_openai_api_key="mock",
        azure_openai_deployment_chat="gpt-4.1",
        azure_openai_deployment_chat_mini="gpt-4.1-mini",
        token_limit=100
    )
    
    # Mock AI Client
    ai_client = MagicMock(spec=AzureAIClient)
    chat_response = ChatResult(
        content="AI solved 2+2=4",
        finish_reason="stop",
        prompt_tokens=20,
        completion_tokens=10,
        total_tokens=30,
        model="gpt-4.1",
    )
    ai_client.chat = AsyncMock(return_value=chat_response)
    ai_client.chat_json = AsyncMock(return_value={
        "intent": "question",
        "entities": [],
        "complexity": "simple",
        "language": "en",
        "suggested_model": "gpt-4.1-mini"
    })

    token_counter = TokenCounter(settings)
    retrieval_engine = MagicMock()
    
    # Mock empty retrieval search
    retrieval_engine.search = AsyncMock(return_value=[])
    
    ranking_engine = MagicMock()
    ranking_engine.rank = MagicMock(return_value=[])

    # Setup database mocks for WorkspaceDetector & VariableResolver
    workspace = Workspace(id="ws-1", name="Math Lab", slug="math-lab", is_default=1)
    
    db_result = MagicMock()
    db_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[workspace])))
    db_result.scalar_one_or_none = MagicMock(return_value=workspace)
    db.execute = AsyncMock(return_value=db_result)

    orchestrator = PipelineOrchestrator(
        db=db,
        settings=settings,
        ai_client=ai_client,
        token_counter=token_counter,
        retrieval_engine=retrieval_engine,
        ranking_engine=ranking_engine
    )

    # Execute
    input_payload = PipelineInput(user_message="what is 2+2?", workspace_id="ws-1")
    output = await orchestrator.execute(input_payload)

    assert output.ai_response == "AI solved 2+2=4"
    assert output.token_usage is not None
    assert output.token_usage.total == 30
    assert len(output.pipeline_trace) > 0
    # Last step in trace should be the OpenAI call
    assert output.pipeline_trace[-1].step_name == "azure_openai_chat"
