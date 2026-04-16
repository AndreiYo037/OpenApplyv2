"""API schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    job_text: str
    cv_text: str


class Contact(BaseModel):
    name: str
    role: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    source: str
    confidence: float
    search_hint: str


class FinalOutput(BaseModel):
    title: str
    company: str
    job_fit: float
    contact_score: float
    final_score: float
    contacts: List[Contact]
    decision: str
    action_plan: str
    actionable: bool
    discard_reason: Optional[str] = None
    company_signals: List[str] = Field(default_factory=list)
