"""Core API request and response schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    skills: List[str]
    experience: str
    education: str
    projects: List[str]


class JobInput(BaseModel):
    job_text: str
    user_profile: UserProfile


class Contact(BaseModel):
    name: str
    role: str
    score: float
    reason: str


class ScoreBreakdown(BaseModel):
    cv_match: dict
    contact_components: dict = Field(default_factory=dict)


class FinalOutput(BaseModel):
    final_score: int
    cv_score: float
    contact_quality: float
    contacts: List[Contact]
    message: str
    score_breakdown: ScoreBreakdown
