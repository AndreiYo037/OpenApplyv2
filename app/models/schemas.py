"""Core API request and response schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


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
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    relevance_score: Optional[float] = None


class FinalOutput(BaseModel):
    title: str
    company: str
    job_fit: float
    contact_score: float
    final_score: float
    contacts: List[Contact]
    decision: str
    action_plan: str
