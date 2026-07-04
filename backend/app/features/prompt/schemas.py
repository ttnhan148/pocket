"""Pydantic schemas for Prompt Compilation endpoints."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel


class PromptCompileRequest(BaseModel):
    workspace_id: str
    user_message: str
    selected_context_ids: Optional[List[str]] = None
    variable_overrides: Optional[Dict[str, str]] = None


class ValidationCheckDetail(BaseModel):
    name: str
    passed: bool
    severity: str
    message: str
    suggestion: Optional[str] = None


class ValidationResultDetail(BaseModel):
    passed: bool
    errors: List[ValidationCheckDetail]
    warnings: List[ValidationCheckDetail]


class PromptScoreDetail(BaseModel):
    overall: float
    clarity: float
    specificity: float
    completeness: float
    consistency: float
    efficiency: float
    reasoning: str
    suggestions: List[str]


class PromptCompileResponse(BaseModel):
    final_prompt: str
    system_prompt: str
    variables_resolved: Dict[str, str]
    validation_result: Optional[ValidationResultDetail] = None
    prompt_score: Optional[PromptScoreDetail] = None
