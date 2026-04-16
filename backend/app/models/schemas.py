"""API schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    job_text: str
    cv_text: str


class Contact(BaseModel):
    id: Optional[str] = None
    name: str
    role: Optional[str] = None
    role_type: Optional[str] = None
    influence_level: Optional[float] = None
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
    job_summary: str = ""
    required_skills: List[str] = Field(default_factory=list)


class GenerateMessageInput(BaseModel):
    contact_id: str
    cv: dict
    job: dict
    company_intel: dict
    contact: Contact
    user_preferences: dict = Field(default_factory=dict)


class GenerateMessageOutput(BaseModel):
    message: str
    personalization_points: List[str] = Field(default_factory=list)
    effectiveness_breakdown: dict = Field(default_factory=dict)
