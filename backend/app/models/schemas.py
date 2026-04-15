"""API schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    job_text: str
    cv_text: str


class Contact(BaseModel):
    id: str
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
    cv_score: float
    contact_quality: float
    final_score: float
    contacts: List[Contact]
    company_signals: List[str] = Field(default_factory=list)


class GenerateMessageInput(BaseModel):
    contact_id: str
    cv: Dict[str, Any]
    job: Dict[str, Any]
    company_intel: Dict[str, Any]
    contact: Dict[str, Any]
    user_preferences: Dict[str, Any] = Field(default_factory=dict)


class GenerateMessageOutput(BaseModel):
    message: str
    personalization_points: List[str] = Field(default_factory=list)
    effectiveness_breakdown: Dict[str, Any] = Field(default_factory=dict)
